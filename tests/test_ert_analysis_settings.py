from types import SimpleNamespace
from typing import List, Optional

import pytest

from flownet.ert._create_ert_setup import _TEMPLATE_ENVIRONMENT


def _render(
    enabled: bool = False,
    threshold: Optional[float] = None,
    auto_scale: Optional[List[str]] = None,
) -> str:
    config = SimpleNamespace(
        ert=SimpleNamespace(
            realizations=SimpleNamespace(
                num_realizations=2, required_success_percent=20, max_runtime=300
            ),
            queue=SimpleNamespace(
                system="LOCAL", name=None, server=None, max_running=2
            ),
            runpath="runpath/realization-<IENS>/iter-<ITER>",
            enspath="output/storage",
            eclbase="eclipse/model/FLOWNET_REALIZATION",
            analysis=[],
            localization=SimpleNamespace(
                enabled=enabled, correlation_threshold=threshold
            ),
            auto_scale=auto_scale or [],
        )
    )
    return _TEMPLATE_ENVIRONMENT.get_template("ahm_config.ert.jinja2").render(
        {
            "config": config,
            "random_seed": None,
            "debug": False,
            "pickled_network": "network.pickled",
            "pickled_schedule": "schedule.pickled",
            "pickled_parameters": "parameters.pickled",
            "pred_schedule_file": None,
        }
    )


def _analysis_lines(rendered: str) -> List[str]:
    return [line for line in rendered.splitlines() if "ANALYSIS_SET_VAR" in line]


def test_defaults_do_not_change_ert_config() -> None:
    assert not _analysis_lines(_render())


def test_localization_and_auto_scale_rendered() -> None:
    lines = _analysis_lines(
        _render(enabled=True, threshold=0.5, auto_scale=["WOPR_*", "FOPR,FWPR"])
    )
    assert lines == [
        "ANALYSIS_SET_VAR STD_ENKF LOCALIZATION TRUE",
        "ANALYSIS_SET_VAR STD_ENKF LOCALIZATION_CORRELATION_THRESHOLD 0.5",
        "ANALYSIS_SET_VAR OBSERVATIONS AUTO_SCALE WOPR_*",
        "ANALYSIS_SET_VAR OBSERVATIONS AUTO_SCALE FOPR,FWPR",
    ]


def test_threshold_ignored_without_localization() -> None:
    assert not _analysis_lines(_render(enabled=False, threshold=0.5))


def test_ert_accepts_rendered_settings() -> None:
    analysis_config = pytest.importorskip("ert.config.analysis_config")
    lines = _analysis_lines(_render(enabled=True, threshold=0.5, auto_scale=["WOPR_*"]))
    analysis_set_var = [line.split(maxsplit=3)[1:] for line in lines]
    config = analysis_config.AnalysisConfig.from_dict(
        {"NUM_REALIZATIONS": 2, "ANALYSIS_SET_VAR": analysis_set_var}
    )
    es_settings = config.es_settings
    assert config.parameter_type_update_strategies["GEN_KW"].value == "adaptive"
    assert es_settings.localization is True
    assert es_settings.localization_correlation_threshold == 0.5
    assert config.observation_settings.auto_scale_observations == [["WOPR_*"]]
