"""
This is where the implementation of the plugin code goes.
The -class is imported from both run_plugin.py and run_debug.py
"""
import sys
import os
import time
import csv
import json
import logging
import subprocess
import xml.etree.ElementTree as ET
from io import StringIO
from webgme_bindings import PluginBase

# Setup a logger
logger = logging.getLogger('')
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)  # By default it logs to stderr..
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class OpenSeesTransformation(PluginBase):
    def __init__(self, *args, **kwargs):
        self.config = None
        self.model = None
        super(OpenSeesTransformation, self).__init__(*args, **kwargs)

    def main(self):
        active_node = self.active_node
        core = self.core
        logger = self.logger
        self.config = self.get_current_config()

        META = {}
        METANodes = core.get_all_meta_nodes(active_node)
        for path in METANodes:
            node = METANodes[path]
            META[core.get_attribute(node, 'name')] = node

        children = core.load_children(active_node)
        self.model = {'name': core.get_attribute(active_node, 'name'),
                      'metadata': {},
                      'constant': [],
                      'basicbuilder': {},
                      'node': [],
                      'geomTransf': [],
                      'element': [],
                      'analysis_pack': [],
                      }

        # Let's categorize each child in the model
        for child in children:
            if core.is_type_of(child, META['MetaData']):
                self.process_metadata(child)
            elif core.is_type_of(child, META['constant']):
                self.process_constant(child)
            elif core.is_type_of(child, META['BasicBuilder']):
                self.process_basicBuilder(child)
            elif core.is_type_of(child, META['node']):
                self.process_node(child)
            elif core.is_type_of(child, META['geomTransf']):
                self.process_geomtransf(child)
            elif core.is_type_of(child, META['element']):
                self.process_element(child)
            elif core.is_type_of(child, META['rayleigh']):
                self.process_rayleigh(child)
            elif core.is_type_of(child, META['analysis_pack']):
                self.process_analysis_pack(child)
            else:
                logger.error("This is not a building block "
                             "I am familiar with.\n"
                             "Most probably, this is a "
                             "documentation composition")

        os_code = self.get_code()
        logger.info(self.get_code())
        self.save_code(os_code)

        if self.config['simulate']:
            self.simulate_model(os_code)

    def process_metadata(self, node):
        model_data = {
            'description': self.core.get_attribute(node, 'analysis_description'),
            'name': self.core.get_attribute(node, 'analysis_name'),
            'type': self.core.get_attribute(node, 'analysis_type'),
            'unit_system': self.core.get_attribute(node, 'unit_system'),
            'author': self.core.get_attribute(node, 'author'),
            'date': self.core.get_attribute(node, 'date'),
        }

        self.model['metadata'] = model_data

    def process_constant(self, node):
        model_data = {
            'name': self.core.get_attribute(node, 'expression'),
            'parameter': self.core.get_attribute(node, 'value'),
            'comment': self.core.get_attribute(node, 'comment'),
        }

        self.model['constant'].append(model_data)

    def process_basicBuilder(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'ndf': self.core.get_attribute(node, 'ndf'),
            'ndm': self.core.get_attribute(node, 'ndm'),
        }

        self.model['basicbuilder'] = model_data

    def process_node(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'coords_dof1': self.core.get_attribute(node, 'coords_dof1'),
            'coords_dof2': self.core.get_attribute(node, 'coords_dof2'),
            'fix_dof1': self.core.get_attribute(node, 'fix_dof1'),
            'fix_dof2': self.core.get_attribute(node, 'fix_dof2'),
            'fix_dof3': self.core.get_attribute(node, 'fix_dof3'),
            'mass_dof1': self.core.get_attribute(node, 'mass_dof1'),
            'mass_dof2': self.core.get_attribute(node, 'mass_dof2'),
            'mass_dof3': self.core.get_attribute(node, 'mass_dof3'),
            'nodeTag': self.core.get_attribute(node, 'nodeTag'),
        }

        self.model['node'].append(model_data)

    def process_geomtransf(self, node):
        model_data = {
            'transfTag': self.core.get_attribute(node, 'transfTag'),
            'transfType': self.core.get_attribute(node, 'name')[11:],
            'comment': self.core.get_attribute(node, 'comment'),
        }

        self.model['geomTransf'].append(model_data)

    def process_element(self, node):
        src = self.core.load_pointer(node, 'src')
        dst = self.core.load_pointer(node, 'dst')

        if self.core.is_type_of(node, self.META['elasticBeamColumn']):
            model_data = {
                'comment': self.core.get_attribute(node, 'comment'),
                'eleType': self.core.get_attribute(node, 'name'),
                'eleTag': self.core.get_attribute(node, 'eleTag'),
                'A': self.core.get_attribute(node, 'A'),
                'E': self.core.get_attribute(node, 'E'),
                'Iz': self.core.get_attribute(node, 'Iz'),
                'cMass': self.core.get_attribute(node, 'cMass'),
                'massDens': self.core.get_attribute(node, 'massDens'),
                'transfTag': self.core.get_attribute(node, 'transfTag'),
                'src': self.core.get_attribute(src, 'nodeTag'),
                'dst': self.core.get_attribute(dst, 'nodeTag'),
            }

        self.model['element'].append(model_data)

    def process_rayleigh(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'a': self.core.get_attribute(node, 'a'),
            'b': self.core.get_attribute(node, 'b'),
            'c': self.core.get_attribute(node, 'c'),
            'd': self.core.get_attribute(node, 'd'),
        }

        self.model['rayleigh'] = model_data

    def process_analysis_pack(self, node):
        children = self.core.load_children(node)

        model_data = {
            'analysis_order': self.core.get_attribute(node, 'analysis_order'),
            'comment': self.core.get_attribute(node, 'comment'),
        }

        for child in children:
            if self.core.is_type_of(child, self.META['loadConst']):
                model_data['loadConst'] = self.process_loadconst(child)
            elif self.core.is_type_of(child, self.META['timeSeries']):
                model_data['timeSeries'] = self.process_timeseries(child)
            elif self.core.is_type_of(child, self.META['pattern']):
                model_data['pattern'] = self.process_pattern(child)
            elif self.core.is_type_of(child, self.META['system']):
                model_data['system'] = self.process_system(child)
            elif self.core.is_type_of(child, self.META['numberer']):
                model_data['numberer'] = self.process_numberer(child)
            elif self.core.is_type_of(child, self.META['constraints']):
                model_data['constraints'] = self.process_constraints(child)
            elif self.core.is_type_of(child, self.META['integrator']):
                model_data['integrator'] = self.process_integrator(child)
            elif self.core.is_type_of(child, self.META['test']):
                model_data['test'] = self.process_test(child)
            elif self.core.is_type_of(child, self.META['algorithm']):
                model_data['algorithm'] = self.process_algorithm(child)
            elif self.core.is_type_of(child, self.META['analysis']):
                model_data['analysis'] = self.process_analysis(child)
            elif self.core.is_type_of(child, self.META['analyze']):
                model_data['analyze'] = self.process_analyze(child)
            elif self.core.is_type_of(child, self.META['recorder']):
                model_data.setdefault('recorder', []).append(self.process_recorder(child))
            else:
                logger.error("This is not a building block "
                             "I am familiar with.")

        self.model['analysis_pack'].append(model_data)

    def process_loadconst(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'pseudoTime': self.core.get_attribute(node, 'pseudoTime'),
        }

        return model_data

    def process_timeseries(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'tsType': self.core.get_attribute(node, 'name')[11:],
            'tag': self.core.get_attribute(node, 'tag'),
        }
        if self.core.get_attribute(node, 'name')[11:] == 'Path File':
            model_data['cFactor'] = self.core.get_attribute(node, 'cFactor')
            model_data['dt'] = self.core.get_attribute(node, 'dt')
            model_data['filePath'] = self.core.get_attribute(node, 'filePath')
            model_data['tsType'] = 'Path'

        return model_data

    def process_pattern(self, node):
        children = self.core.load_children(node)

        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'tsType': self.core.get_attribute(node, 'name')[8:],
            'tsTag': self.core.get_attribute(node, 'tsTag'),
            'patternTag': self.core.get_attribute(node, 'patternTag'),
        }

        for child in children:
            if self.core.is_type_of(child, self.META['load element single/multiple']):
                model_data.setdefault('eleLoad', []).append(self.process_loadelement(child))
            elif self.core.is_type_of(child, self.META['load node']):
                model_data.setdefault('nodeLoad', []).append(self.process_loadnode(child))

        if model_data['tsType'] == 'UniformExcitation':
            model_data['dir'] = self.core.get_attribute(node, 'dir')

        return model_data

    def process_loadelement(self, node):
        model_data = {
            'Wy': self.core.get_attribute(node, 'Wy'),
            'eleTag': self.core.get_attribute(node, 'eleTag'),
        }

        return model_data

    def process_loadnode(self, node):
        model_data = {
            'loadvalues': self.core.get_attribute(node, 'loadvalues'),
            'nodeTag': self.core.get_attribute(node, 'nodeTag'),
        }

        return model_data

    def process_system(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'name': self.core.get_attribute(node, 'name')[7:],
        }

        return model_data

    def process_numberer(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'name': self.core.get_attribute(node, 'name')[9:],
        }

        return model_data

    def process_constraints(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'name': self.core.get_attribute(node, 'name')[12:],
        }

        return model_data

    def process_integrator(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'name': self.core.get_attribute(node, 'name')[11:],
        }
        if model_data['name'] == 'LoadControl':
            model_data['lambda'] = self.core.get_attribute(node, 'lambda')
        if model_data['name'] == 'Newmark':
            model_data['beta'] = self.core.get_attribute(node, 'beta')
            model_data['gamma'] = self.core.get_attribute(node, 'gamma')

        return model_data

    def process_test(self, node):
        model_data = {
            'comment': self.core.get_attribute(node, 'comment'),
            'name': self.core.get_attribute(node, 'name')[5:],
            'tol': self.core.get_attribute(node, 'tol'),
            'iter': self.core.get_attribute(node, 'iter'),
        }

        return model_data

    def process_algorithm(self, node):
        model_data = {
            'name': self.core.get_attribute(node, 'name')[10:],
            'comment': self.core.get_attribute(node, 'comment'),
        }

        return model_data

    def process_analysis(self, node):
        model_data = {
            'name': self.core.get_attribute(node, 'name')[9:],
            'comment': self.core.get_attribute(node, 'comment'),
        }

        return model_data

    def process_analyze(self, node):
        model_data = {
            'numIncr': self.core.get_attribute(node, 'numIncr'),
            'comment': self.core.get_attribute(node, 'comment'),
        }

        if self.core.get_attribute(node, 'dT'):
            model_data['dT'] = self.core.get_attribute(node, 'dT')

        return model_data

    def process_recorder(self, node):
        if self.core.is_type_of(node, self.META['recorder Element']):
            model_data = {
                'name': self.core.get_attribute(node, 'name')[9:],
                'file': self.core.get_attribute(node, 'file'),
                'fileName': self.core.get_attribute(node, 'fileName'),
                'ele': self.core.get_attribute(node, 'ele'),
                'respType': self.core.get_attribute(node, 'respType'),
                'comment': self.core.get_attribute(node, 'comment'),
            }

        if self.core.is_type_of(node, self.META['recorder Node']):
            model_data = {
                'name': self.core.get_attribute(node, 'name')[9:],
                'file': self.core.get_attribute(node, 'file'),
                'fileName': self.core.get_attribute(node, 'fileName'),
                'startNode': self.core.get_attribute(node, 'startNode'),
                'endNode': self.core.get_attribute(node, 'endNode'),
                'disp': self.core.get_attribute(node, 'disp'),
                'dof': self.core.get_attribute(node, 'dof'),
                'comment': self.core.get_attribute(node, 'comment'),
                'time': self.core.get_attribute(node, 'time'),
            }

        return model_data

    def get_code(self):
        code_text = '# ' + self.model['name'] + '\n'

        # metadata
        code_text += '# Analysis Name: ' + self.model['metadata']['name'] + '\n'
        code_text += '# Analysis Description: ' + self.model['metadata']['description'] + '\n'
        code_text += '# Analysis Type: ' + self.model['metadata']['type'] + '\n'
        code_text += '#--------\n'
        code_text += '# Author: ' + self.model['metadata']['author'] + '\n'
        code_text += '# Unit System: ' + self.model['metadata']['unit_system'] + '\n'
        code_text += '# Date: ' + self.model['metadata']['date'] + '\n'

        # constants
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Set constants\n'
        code_text += '# This is tcl code but ' \
                     'defined in OpenSees domain\n'
        self.model['constant'].sort(key=lambda t: t['name'])
        for constant in self.model['constant']:
            if constant['name'] != 'freq':  # we can't determine eigen value without the full model
                code_text += 'set ' + constant['name'] + ' [expr ' + constant['parameter'] + ']'
                if constant['comment']:
                    code_text += '; # ' + constant['comment'] + '\n'
                else:
                    code_text += '\n'

        # model builder
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Set ModelBuilder\n'
        code_text += 'model ' + 'BasicBuilder' + \
                     ' -ndm ' + str(self.model['basicbuilder']['ndm']) + \
                     ' -ndf ' + str(self.model['basicbuilder']['ndf']) + \
                     '; # ' + self.model['basicbuilder']['comment'] + '\n'

        # nodes
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Create nodes & add to Domain\n'
        code_text += '# command: node nodeId xCrd yCrd <-mass $massX $massY $massRz>\n'
        code_text += '# NOTE: mass in optional\n'
        self.model['node'].sort(key=lambda t: t['nodeTag'])
        for node in self.model['node']:
            code_text += 'node ' + str(node['nodeTag']) + ' ' + \
                         node['coords_dof1'] + ' ' + node['coords_dof2']
            if node['mass_dof1']:
                code_text += ' -mass ' + node['mass_dof1'] + ' ' + node['mass_dof2'] + ' ' + node['mass_dof3'] + '\n'
            else:
                code_text += '\n'

        # fixes
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Set the boundary conditions - command\n'
        code_text += '# command: fix nodeID xResrnt? yRestrnt? rZRestrnt?\n'
        for node in self.model['node']:
            if (node['fix_dof1'] or node['fix_dof2'] or node['fix_dof3']):
                code_text += 'fix ' + str(node['nodeTag']) + \
                             ' ' + str(int(node['fix_dof1'])) + \
                             ' ' + str(int(node['fix_dof2'])) + \
                             ' ' + str(int(node['fix_dof3'])) + \
                             '\n'

        # geometric transformations
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Define geometric transformations\n'
        self.model['geomTransf'].sort(key=lambda t: t['transfTag'])
        for geomTransf in self.model['geomTransf']:
            code_text += 'geomTransf ' + geomTransf['transfType'] + ' ' + str(geomTransf['transfTag'])
            if geomTransf['comment']:
                code_text += '; # ' + geomTransf['comment'] + '\n'
            else:
                code_text += '\n'

        # elements
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Define elements\n'
        self.model['element'].sort(key=lambda t: t['eleTag'])
        for element in self.model['element']:
            code_text += 'element ' + element['eleType'] + ' ' + str(element['eleTag']) + \
                         ' ' + str(element['src']) + ' ' + str(element['dst']) + \
                         ' ' + element['A'] + ' ' + element['E'] + \
                         ' ' + element['Iz'] + ' ' + str(element['transfTag'])
            if element['comment']:
                code_text += '; # ' + element['comment'] + '\n'
            else:
                code_text += '\n'

        # rayleigh
        if 'rayleigh' in self.model:
            code_text += '\n'
            code_text += '#--------\n'
            code_text += '# Define rayleigh damping - for transient analysis\n'

            for constant in self.model['constant']:
                if constant['name'] == 'freq':  # we can't determine eigen value without the full model
                    code_text += 'set ' + constant['name'] + ' [expr ' + constant['parameter'] + ']'
                    if constant['comment']:
                        code_text += '; # ' + constant['comment'] + '\n'
                    else:
                        code_text += '\n'

            code_text += 'rayleigh ' + \
                         '[expr ' + self.model['rayleigh']['a'] + '] ' + \
                         '[expr ' + self.model['rayleigh']['b'] + '] ' + \
                         '[expr ' + self.model['rayleigh']['c'] + '] ' + \
                         '[expr ' + self.model['rayleigh']['d'] + ']'
            if element['comment']:
                code_text += '; # ' + self.model['rayleigh']['comment'] + '\n'
            else:
                code_text += '\n'

        # analysis pack
        code_text += '\n'
        code_text += '#--------\n'
        code_text += '# Define analysis\n'
        self.model['analysis_pack'].sort(key=lambda t: t['analysis_order'])
        for analysis_pack in self.model['analysis_pack']:
            # initial comment
            code_text += '# ' + analysis_pack['comment'] + '\n'

            # setting time
            if 'loadConst' in analysis_pack:
                code_text += 'loadConst -time ' + analysis_pack['loadConst']['pseudoTime']
                if analysis_pack['timeSeries']['comment']:
                    code_text += '; # ' + analysis_pack['loadConst']['comment'] + '\n\n'
                else:
                    code_text += '\n\n'

            # timeseries
            if analysis_pack['timeSeries']['tsType'] == 'Path':
                eq_filepath = os.path.join(os.getcwd(), 'OpenSees', analysis_pack['timeSeries']['filePath'])
                code_text += 'timeSeries ' + analysis_pack['timeSeries']['tsType'] + ' ' + \
                             str(analysis_pack['timeSeries']['tag']) + \
                             ' -dt ' + analysis_pack['timeSeries']['dt'] + \
                             ' -filePath ' + eq_filepath.replace('\\', '\\\\') + \
                             ' -factor [expr ' + analysis_pack['timeSeries']['cFactor'] + ']'

            else:
                code_text += 'timeSeries ' + analysis_pack['timeSeries']['tsType'] + ' ' + \
                             str(analysis_pack['timeSeries']['tag'])
            if analysis_pack['timeSeries']['comment']:
                code_text += '; # ' + analysis_pack['timeSeries']['comment'] + '\n\n'
            else:
                code_text += '\n\n'

            # pattern definition
            if analysis_pack['pattern']['comment']:
                code_text += '# ' + analysis_pack['pattern']['comment'] + '\n'
            if analysis_pack['pattern']['tsType'] == 'UniformExcitation':
                code_text += 'pattern ' + analysis_pack['pattern']['tsType'] + ' ' + \
                             str(analysis_pack['pattern']['patternTag']) + ' ' + \
                             str(analysis_pack['pattern']['dir']) + \
                             ' -accel ' + str(analysis_pack['pattern']['tsTag']) + \
                             '\n\n'
            else:
                code_text += 'pattern ' + analysis_pack['pattern']['tsType'] + ' ' + \
                             str(analysis_pack['pattern']['patternTag']) + ' ' + \
                             str(analysis_pack['pattern']['tsTag'])
                code_text += ' {\n'

                # loads
                if 'eleLoad' in analysis_pack['pattern']:
                    analysis_pack['pattern']['eleLoad'].sort(key=lambda t: t['Wy'])
                    for eleLoad in analysis_pack['pattern']['eleLoad']:
                        code_text += '    eleLoad -ele ' + eleLoad['eleTag'] + \
                                     ' -type -beamUniform ' + eleLoad['Wy'] + '\n'
                if 'nodeLoad' in analysis_pack['pattern']:
                    analysis_pack['pattern']['nodeLoad'].sort(key=lambda t: t['loadvalues'])
                    for nodeLoad in analysis_pack['pattern']['nodeLoad']:
                        code_text += '    load ' + str(nodeLoad['nodeTag']) + ' ' + nodeLoad['loadvalues'] + '\n'
                code_text += '}\n\n'

            # solver settings
            code_text += '#--------\n'
            code_text += '# Define analysis solver settings\n'

            # solvers - system
            code_text += 'system ' + analysis_pack['system']['name']
            if analysis_pack['system']['comment']:
                code_text += '; # ' + analysis_pack['system']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - numberer
            code_text += 'numberer ' + analysis_pack['numberer']['name']
            if analysis_pack['numberer']['comment']:
                code_text += '; # ' + analysis_pack['numberer']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - constraints
            code_text += 'constraints ' + analysis_pack['constraints']['name']
            if analysis_pack['constraints']['comment']:
                code_text += '; # ' + analysis_pack['constraints']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - integrator
            if analysis_pack['integrator']['name'] == 'LoadControl':
                code_text += 'integrator ' + analysis_pack['integrator']['name'] + ' ' + \
                             str(analysis_pack['integrator']['lambda'])
            if analysis_pack['integrator']['name'] == 'Newmark':
                code_text += 'integrator ' + analysis_pack['integrator']['name'] + ' ' + \
                             str(analysis_pack['integrator']['gamma']) + ' ' + \
                             str(analysis_pack['integrator']['beta'])
            if analysis_pack['integrator']['comment']:
                code_text += '; # ' + analysis_pack['integrator']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - test
            code_text += 'test ' + analysis_pack['test']['name'] + ' ' + \
                         str(analysis_pack['test']['tol']) + ' ' + \
                         str(analysis_pack['test']['iter'])
            if analysis_pack['test']['comment']:
                code_text += '; # ' + analysis_pack['test']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - algorithm
            code_text += 'algorithm ' + analysis_pack['algorithm']['name']
            if analysis_pack['algorithm']['comment']:
                code_text += '; # ' + analysis_pack['algorithm']['comment'] + '\n'
            else:
                code_text += '\n'

            # solvers - analysis
            code_text += 'analysis ' + analysis_pack['analysis']['name']
            if analysis_pack['analysis']['comment']:
                code_text += '; # ' + analysis_pack['analysis']['comment'] + '\n\n'
            else:
                code_text += '\n\n'

                # recorders to obtain responses
                if 'recorder' in analysis_pack:
                    for recorder in analysis_pack['recorder']:
                        if (recorder['name'] == 'Element'):
                            code_text += 'recorder Element' + \
                                         ' -file ' + recorder['fileName'] + \
                                         ' -ele ' + recorder['ele'] + \
                                         ' ' + recorder['respType']
                            if recorder['comment']:
                                code_text += '; # ' + recorder['comment'] + '\n'
                            else:
                                code_text += '\n'
                        if (recorder['name'] == 'Node'):
                            code_text += 'recorder Node' + \
                                         ' -xml ' + recorder['fileName']
                            if recorder['time']:
                                code_text += ' -time'
                            code_text += ' -nodeRange ' + str(recorder['startNode']) + ' ' + \
                                         str(recorder['endNode']) + \
                                         ' -dof ' + recorder['dof']
                            if (recorder['disp']):
                                code_text += ' disp'
                            if recorder['comment']:
                                code_text += '; # ' + recorder['comment'] + '\n'
                            else:
                                code_text += '\n'

            # solvers - analyze
            code_text += '\n'
            code_text += 'analyze ' + '[expr ' + str(analysis_pack['analyze']['numIncr']) + \
                         ']'
            if analysis_pack['analysis']['name'] == 'Transient':
                code_text += ' ' + str(analysis_pack['analyze']['dT'])

            if analysis_pack['analyze']['comment']:
                code_text += '; # ' + analysis_pack['analyze']['comment'] + '\n\n\n'
            else:
                code_text += '\n\n\n'

        return code_text

    def save_code(self, os_code):
        self.add_file(self.model['name'] + '.tcl', os_code)

    def simulate_model(self, os_code):
        logger.info('## Will simulate model ##')
        sim_dir = os.path.join(os.getcwd(), 'outputs', '{0} {1}'.format(self.model['name'], time.time()))
        os.makedirs(sim_dir, exist_ok=True)

        os_path = os.path.join(sim_dir, '{0}.tcl'.format(self.model['name']))
        with open(os_path, 'w') as f:
            f.write(os_code)

        sim_exe = os.path.join(os.getcwd(), 'OpenSees', 'OpenSees.exe')

        subprocess.check_call([sim_exe, os_path], cwd=sim_dir)

        sim_res = self.read_sim_results(sim_dir)
        # logger.info('TimeSeries {0}'.format(json.dumps(sim_res, indent=2)))

        result_hash = self.add_file('res.json', json.dumps(sim_res, indent=2))

        self.core.set_attribute(self.active_node, 'simRes', result_hash)

        self.util.save(self.root_node, self.commit_hash, 'master', 'Attached result in model')

    def read_sim_results(self, sim_dir):
        csv_path = os.path.join(sim_dir, 'NodeDisp.out')
        result = {
            'commitHash': self.commit_hash,
            'timeStamp': time.time(),
            'timeSeries': {}
        }

        tree = ET.parse(csv_path)
        root = tree.getroot()
        scsv = root.find('Data').text

        idx_to_variable = []
        result['timeSeries']['time'] = []
        idx_to_variable.append('time')

        for child in root:
            if child.tag != 'Data':
                variable = child.attrib['nodeTag'] + '-' + child.find('ResponseType').text
                result['timeSeries'][variable] = []
                idx_to_variable.append(variable)

        reader = csv.reader(scsv.split('\n'), skipinitialspace=True, delimiter=' ')

        for row in reader:
            if row:  # first rows may be empty
                for idx, value in enumerate(row):
                    if value:  # last value may be empty
                        result['timeSeries'][idx_to_variable[idx]].append(float(value))

        return result
