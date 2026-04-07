from .base import BaseTask
from .clinical_calc import ClinicalCalcTask
from .biostat_power import BiostatPowerTask
from .biocoder import BiocoderTask

TASK_REGISTRY: dict[str, type[BaseTask]] = {
    "clinical_calc": ClinicalCalcTask,
    "biostat_power": BiostatPowerTask,
    "biocoder": BiocoderTask,
}

__all__ = [
    "BaseTask",
    "ClinicalCalcTask",
    "BiostatPowerTask",
    "BiocoderTask",
    "TASK_REGISTRY",
]
