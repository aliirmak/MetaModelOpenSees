# Meta Modeling for OpenSees
OpenSees, the Open System for Earthquake Engineering Simulation, is an open-source finite element tool that has advanced capabilities for modeling and analyzing linear and nonlinear response of structural and geotechnical systems using a wide range of material models, elements, and solution algorithms. OpenSees is a text-based program and users develop their models by writing scripts in Tcl and employing commands special to OpenSees. The commands for scripts are specific to structural and geotechnical domains. Users can define variables such as geometry, boundary conditions, section size of structural elements, material and behavior of the elements, damping ratios, solvers, input excitations, and many more.

This project seeks to add a basic support to WebGME to run OpenSees models. Using the model-integrated approach, OpenSees models can be now used multiple times to run different simulations. The tool is especially useful for visualizing a structural model instead of using script which may be challenging for first year undergraduate studetens who want to learn how structures are working but don't know how to start.

## How to use this repo
- Follow the standard installation and setup of WebGME (as instructed here https://github.com/webgme/webgme).
- This project assumes your mongodb folder is **webgmeData** under C drive and your application folder is **mywebgmeapp** under C drive.
- There is a plugin called **OpenSeesTransformation** that converts an OpenSees WebGME model into Tcl script. It is located under **src\plugins\OpenSeesTransformation**. Standard entry point for debug is run_debug.py under the same folder. The transformation code is given in **__init__.py** under **src\plugins\OpenSeesTransformation\OpenSeesTransformation**
- Python 3.6 is used. Packages like webgme_binding, sys, os, time, csv, subprocess, signal, atexit, ElementTree, StringIO and logging should be already installed since the transformation code.
- plotly.js is used for visualization. It is already provided in the repo so no need for new installation.
- I believe dumping the content to a freshly created **mywebgmeapp** should make the project work.

## How to run transformation
- There are two examples. One for 2D (pushover) static and the other one is dynamic (earthquake) simulation. 
- Click on the example that you want to play with. Select validplugin as OpenSeesTransformation if not selected.
- Open the example double-clicking on it. Do not click on any block and run OpenSees transformation.
- Under a minute, the plugin will convert the model into an executable Tcl script, run the simulation, and generate outputs.
- After succesful run of the plugin, go to **SimulationResultPlotter** under Vizualizer Selector on the left side. This will show simulation results. The vizualition may take some a minute due to the amount of data.
