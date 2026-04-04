# Idea Notes

## Product Vision

Build a wind farm monitoring digital twin that can be used for:
- realistic SCADA data generation
- control and fault response exploration
- training and demonstration
- algorithm and diagnostics experimentation
- industrial integration testing

## What Makes This Project Valuable

The value is not only showing a dashboard.
The value is producing believable time-series behavior:
- wind changes should produce realistic power and speed responses
- startup and stop should take time
- faults should change temperature, vibration, power, and control behavior
- grid events should affect different turbines differently
- history should explain what happened and when

## Near-Term Idea Direction

### 1. Make History Explainable
Add event markers for:
- grid events
- fault injection and clearing
- operator actions

### 2. Improve Farm-Level Realism
Add:
- gust propagation
- ramp propagation
- direction-shift propagation
- stronger turbine-to-turbine coupling through the wind field

### 3. Improve Diagnostic Quality
Add:
- better vibration signatures
- more detailed cooling behavior
- better electrical behavior under grid disturbances

### 4. Improve Research Usefulness
Allow users to:
- compare turbines under the same event
- export larger history slices
- replay key events
- annotate event windows

## Non-Immediate Ideas

Useful later, but not first:
- maintenance work order workflows
- authentication and deployment features
- deeper AI diagnosis integration
- long-term database migration
