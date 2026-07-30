from .dataclasses import TrialConfig
from .data_management import Loader, Manager
from .modelling import Modeller
from .validating import Validator
from thematic_analysis_model.view.visualizing import Visualizer

from bertopic import BERTopic
import itertools
from pathlib import Path
import uuid
from typing import Union, Any, List, Dict

# clsases around queeing trials, or individual trials

# individual modelling trial
class Trial:
    def __init__(self, loader: Loader, manager: Manager, trial_config: TrialConfig):
        self.trial_config = trial_config
        self.loader = loader
        self.manager = manager

    def run_trial(self):
        self.manager.clean_lancedb()

        # model
        modeller = Modeller(loader=self.loader, manager=self.manager, trial_config=self.trial_config)
        model = modeller.run_modeller(save_reduced_embeddings=True)

        model.save(self.trial_config.model_save_path, serialization='safetensors', save_embedding_model=True)
        model = BERTopic.load(path=self.trial_config.model_save_path, embedding_model='all-MiniLM-L6-v2')

        # embed
        visualizer = Visualizer(manager=self.manager)
        validator = Validator(model=model, loader=self.loader, manager=self.manager, visualizer=visualizer, trial_config=self.trial_config)
        validator.run_validator()

class TrialQueue:
    def __init__(self, loader: Loader, manager: Manager, trial_configs: list[TrialConfig]):
        self.loader = loader
        self.manager = manager
        self.trial_configs = trial_configs

    def run_queue(self):
        count = 0
        total = len(self.trial_configs)

        for config in self.trial_configs:
            count += 1
            print(f'Running Trial {count} / {total}')

            self.manager.reset_modelling_flags()

            trial = Trial(loader=self.loader, manager=self.manager, trial_config=config)
            trial.run_trial()

    @classmethod
    def generate_trial_configs(cls, **kwargs: Union[Any, List[Any]]) -> List[TrialConfig]:
        """
        Generates a list of TrialConfig Pydantic objects by sweeping over any parameters
        passed as lists. Missing optional fields will default to their definitions in TrialConfig.
        
        Trial names are dynamically constructed by appending the swept parameter names
        and values (e.g., 'hdbscan_min_samples_3').
        """
        swept_fields = {}
        static_fields = {}

        # 1. Separate swept fields (passed as non-string lists) from static values
        for key, value in kwargs.items():
            if isinstance(value, list) and not isinstance(value, str):
                swept_fields[key] = value
            else:
                static_fields[key] = value

        # 2. Compute Cartesian product for swept parameter lists
        if swept_fields:
            keys = list(swept_fields.keys())
            combinations = list(itertools.product(*swept_fields.values()))
        else:
            keys = []
            combinations = [()]

        trial_configs = []

        # 3. Generate individual TrialConfig objects
        for trial_idx, combo in enumerate(combinations, start=1):
            combo_dict = dict(zip(keys, combo))
            full_kwargs = {**static_fields, **combo_dict}

            # Build parameter descriptor strings (e.g. "hdbscan_min_samples_3")
            desc_parts = [f"{k}_{v}" for k, v in combo_dict.items() if k != "trial_name"]

            # Construct trial_name
            base_name = static_fields.get("trial_name")
            if "trial_name" in combo_dict:  # If trial_name itself was passed as a swept list
                trial_name = str(combo_dict["trial_name"])
                if desc_parts:
                    trial_name = f"{trial_name}_" + "_".join(desc_parts)
            elif base_name:
                trial_name = f"{base_name}_" + "_".join(desc_parts) if desc_parts else str(base_name)
            elif desc_parts:
                trial_name = "_".join(desc_parts)
            else:
                trial_name = f"trial_{trial_idx}"

            full_kwargs["trial_name"] = trial_name
            full_kwargs["trial_num"] = trial_idx

            # Ensure id_ is populated if not explicitly supplied
            if "id_" not in full_kwargs or full_kwargs["id_"] is None:
                full_kwargs["id_"] = str(uuid.uuid4())

            # Append the trial_name as a subfolder using pathlib
            base_model_path = full_kwargs.get("model_save_path")
            if base_model_path:
                full_kwargs["model_save_path"] = str(Path(base_model_path) / trial_name)

            # Instantiating Pydantic model automatically validates types and applies defaults
            trial_configs.append(TrialConfig(**full_kwargs))

        return trial_configs