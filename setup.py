from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf8") as fh:
    LONG_DESCRIPTION = fh.read()

REQUIREMENTS = [
    "configsuite>=0.6",
    "cwrap~=1.6",
    "opm~=2026.4",
    "ecl~=2.14.5",
    "ecl2df~=0.17.1",
    "ert~=23.0.1",
    "fmu-ensemble~=1.6.11",
    "hyperopt~=0.3.0",
    "matplotlib~=3.1",
    "mlflow>=1.11.0",
    "numpy>=1.17,<2",
    "opentelemetry-sdk~=1.35.0",
    "pandas~=1.0",
    "psutil~=5.7",
    "pykrige~=1.5",
    "pyvista~=0.23",
    "pyyaml~=6.0.3",
    "scikit-learn~=1.9.1",
    "scipy~=1.6",
    "webviz-config~=0.7.2",
    "webviz-config-equinor~=0.2.8",
    "webviz-subsurface~=0.3.2",
    "xlrd<2",
]

TEST_REQUIRES = [
    "black",
    "mypy>=0.761",
    "pylint>=2.3",
    "pyscal>=0.7.4",
    "pytest>=5.3",
    "pytest-cov>=2.8",
    "sphinx",
    "sphinx-rtd-theme",
    "types-PyYAML",
    "pre-commit~=2.9.3",
]

setup(
    name="flownet",
    install_requires=REQUIREMENTS,
    tests_require=TEST_REQUIRES,
    python_requires=">=3.8,<3.12",
    extras_require={"tests": TEST_REQUIRES},
    description="Simplified training of reservoir simulation models",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/equinor/flownet",
    author="R&T Equinor",
    use_scm_version=True,
    package_dir={"": "src"},
    packages=find_packages("src"),
    package_data={
        "flownet": ["templates/*", "static/*", "ert/forward_models/FLOW_SIMULATION"]
    },
    entry_points={
        "ert": ["flow = flownet.ert.forward_models._flow_job"],
        "console_scripts": [
            "flownet=flownet._command_line:main",
            "flownet_render_realization=flownet.ert.forward_models:render_realization",
            "flownet_delete_simulation_output=flownet.ert.forward_models:delete_simulation_output",
            "flownet_run_flow=flownet.ert.forward_models:run_flow",
            "flownet_save_iteration_parameters=flownet.ert.forward_models:save_iteration_parameters",
            "flownet_save_iteration_analytics=flownet.ert.forward_models:save_iteration_analytics",
            "flownet_save_predictions=flownet.ert.forward_models:save_predictions",
            "flownet_plot_results=flownet.utils.plot_results:main",
        ],
    },
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
