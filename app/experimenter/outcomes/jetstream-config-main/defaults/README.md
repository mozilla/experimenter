# Defaults

This directory contains configurations for specific experiment types or platforms with default metrics and statistics that are computed for every experiment. Configuration files in this directory need to be either named after the experiment type or the platform they target.

Changes to these configurations require approval on a pull request.
Once merged, live experiments will get rerun so the new configurations can get applied. Experiments that have been completed in the past **will not be rerun automatically**, manual reruns need to be triggered if necessary.

Avoid making changes to existing metrics, as results might become inconsistent with experiment analysis results computed in the past.
