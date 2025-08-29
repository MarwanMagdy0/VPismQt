# Convert UI files to Python scripts inside vpism/gui/ui_scripts/
pyuic5 -x vpism/resources/load.ui -o vpism/gui/ui_scripts/load.py --from-imports
# Compile the resources.qrc file into Python resources script
pyrcc5 -o vpism/gui/ui_scripts/res_rc.py vpism/resources/res.qrc
