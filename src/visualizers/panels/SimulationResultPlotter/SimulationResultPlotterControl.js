/*globals define, WebGMEGlobal*/
/**
 * Generated by VisualizerGenerator 1.7.0 from webgme on Mon Nov 26 2018 16:35:30 GMT-0600 (Central Standard Time).
 */

define([
    'js/Constants',
    'js/Utils/GMEConcepts',
    'js/NodePropertyNames',
    'blob/BlobClient'
], function (CONSTANTS,
             GMEConcepts,
             nodePropertyNames,
             BlobClient) {

    'use strict';

    var SimulationResultPlotterControl;

    SimulationResultPlotterControl = function (options) {

        this._logger = options.logger.fork('Control');

        this._client = options.client;

        // Initialize core collections and variables
        this._widget = options.widget;

        this._currentNodeId = null;
        this._currentNodeParentId = undefined;

        this._currentHash = null;
        this._currentPlotData = null;
        this._scatteredOn = true;
        this._blobClient = new BlobClient({logger: this._logger.fork('BlobClient')});

        this._initWidgetEventHandlers();

        this._logger.debug('ctor finished');
    };

    SimulationResultPlotterControl.prototype._initWidgetEventHandlers = function () {
    };

    /* * * * * * * * Visualizer content update callbacks * * * * * * * */
    // One major concept here is with managing the territory. The territory
    // defines the parts of the project that the visualizer is interested in
    // (this allows the browser to then only load those relevant parts).
    SimulationResultPlotterControl.prototype.selectedObjectChanged = function (nodeId) {
        var self = this,
            node;

        self._logger.debug('activeObject nodeId \'' + nodeId + '\'');

        // Remove current territory patterns
        if (self._currentNodeId) {
            self._client.removeUI(self._territoryId);
        }

        self._currentNodeId = nodeId;
        self._currentNodeParentId = undefined;
        self._currentHash = null;
        self._currentPlotData = null;

        if (typeof self._currentNodeId === 'string') {
            node = self._client.getNode(nodeId);
            self._currentNodeParentId = node.getParentId();

            // Put new node's info into territory rules
            self._selfPatterns = {};
            self._selfPatterns[nodeId] = {children: 0};  // Territory "rule"

            self._widget.setTitle('Latest simulation results of ' + node.getAttribute('name'));

            if (typeof self._currentNodeParentId === 'string') {
                self.$btnModelHierarchyUp.show();
            } else {
                self.$btnModelHierarchyUp.hide();
            }

            self._territoryId = self._client.addUI(self, function (events) {
                self._eventCallback(events);
            });

            // Update the territory
            self._client.updateTerritory(self._territoryId, self._selfPatterns);
        }
    };

    SimulationResultPlotterControl.prototype._isChanged = function () {
        var node = this._client.getNode(this._currentNodeId);

        if (node == null)
            return false;

        return this._currentHash !== node.getAttribute('simRes');
    };

    SimulationResultPlotterControl.prototype._buildPlotData = function () {
        var self = this,
            node = self._client.getNode(self._currentNodeId),
            hash;

        if (node == null) {
            return;
        }

        self._currentHash = node.getAttribute('simRes');
        hash = self._currentHash;

        if (typeof hash !== 'string') {
            return;
        }

        self._blobClient.getObjectAsJSON(this._currentHash)
            .then(function (rawObject) {
                var timeSeries = rawObject.timeSeries,
                    keys = Object.keys(timeSeries),
                    plot = [],
                    mode = self._scatteredOn ? 'markers' : 'lines+markers';
                if (hash == self._currentHash) {
                    keys.forEach(function (key) {
                        if (key == 'time') {
                            return;
                        }

                        plot.push({x: timeSeries.time, y: timeSeries[key], name: key, mode: mode, marker: {size: 2}});
                    });
                    self._currentPlotData = plot;
                    self._widget.initPlot(self._currentPlotData);
                } else {
                    self._logger.error('Data changed during file read -> no update');
                }
            })
            .catch(function (e) {
                self._logger.error(e);
                self._widget.initPlot(null);
            })
    }

    SimulationResultPlotterControl.prototype._rebuildPlotData = function () {
        var mode = this._scatteredOn ? 'markers' : 'lines+markers';

        if (this._currentPlotData !== null) {
            this._currentPlotData.forEach(function (trace) {
                trace.mode = mode;
            });

            this._widget.initPlot(this._currentPlotData);
        }
    }

    // This next function retrieves the relevant node information for the widget
    SimulationResultPlotterControl.prototype._getObjectDescriptor = function (nodeId) {
        var node = this._client.getNode(nodeId),
            objDescriptor;
        if (node) {
            objDescriptor = {
                id: node.getId(),
                name: node.getAttribute(nodePropertyNames.Attributes.name),
                childrenIds: node.getChildrenIds(),
                parentId: node.getParentId(),
                isConnection: GMEConcepts.isConnection(nodeId)
            };
        }

        return objDescriptor;
    };

    /* * * * * * * * Node Event Handling * * * * * * * */
    SimulationResultPlotterControl.prototype._eventCallback = function (events) {
        var i = events ? events.length : 0,
            event;

        this._logger.debug('_eventCallback \'' + i + '\' items');

        while (i--) {
            event = events[i];
            switch (event.etype) {

                case CONSTANTS.TERRITORY_EVENT_LOAD:
                    this._onLoad(event.eid);
                    break;
                case CONSTANTS.TERRITORY_EVENT_UPDATE:
                    this._onUpdate(event.eid);
                    break;
                case CONSTANTS.TERRITORY_EVENT_UNLOAD:
                    this._onUnload(event.eid);
                    break;
                default:
                    break;
            }
        }

        this._logger.debug('_eventCallback \'' + events.length + '\' items - DONE');
    };

    SimulationResultPlotterControl.prototype._onLoad = function (gmeId) {
        this._buildPlotData();
    };

    SimulationResultPlotterControl.prototype._onUpdate = function (gmeId) {
        if (this._isChanged()) {
            this._buildPlotData();
        }
    };

    SimulationResultPlotterControl.prototype._onUnload = function (gmeId) {
        this._widget.initPlot(null);
    };

    SimulationResultPlotterControl.prototype._stateActiveObjectChanged = function (model, activeObjectId) {
        if (this._currentNodeId === activeObjectId) {
            // The same node selected as before - do not trigger
        } else {
            this.selectedObjectChanged(activeObjectId);
        }
    };

    /* * * * * * * * Visualizer life cycle callbacks * * * * * * * */
    SimulationResultPlotterControl.prototype.destroy = function () {
        this._detachClientEventListeners();
        this._removeToolbarItems();
    };

    SimulationResultPlotterControl.prototype._attachClientEventListeners = function () {
        this._detachClientEventListeners();
        WebGMEGlobal.State.on('change:' + CONSTANTS.STATE_ACTIVE_OBJECT, this._stateActiveObjectChanged, this);
    };

    SimulationResultPlotterControl.prototype._detachClientEventListeners = function () {
        WebGMEGlobal.State.off('change:' + CONSTANTS.STATE_ACTIVE_OBJECT, this._stateActiveObjectChanged);
    };

    SimulationResultPlotterControl.prototype.onActivate = function () {
        this._attachClientEventListeners();
        this._displayToolbarItems();

        if (typeof this._currentNodeId === 'string') {
            WebGMEGlobal.State.registerActiveObject(this._currentNodeId, {suppressVisualizerFromNode: true});
        }
    };

    SimulationResultPlotterControl.prototype.onDeactivate = function () {
        this._detachClientEventListeners();
        this._hideToolbarItems();
    };

    /* * * * * * * * * * Updating the toolbar * * * * * * * * * */
    SimulationResultPlotterControl.prototype._displayToolbarItems = function () {

        if (this._toolbarInitialized === true) {
            for (var i = this._toolbarItems.length; i--;) {
                this._toolbarItems[i].show();
            }
        } else {
            this._initializeToolbar();
        }
    };

    SimulationResultPlotterControl.prototype._hideToolbarItems = function () {

        if (this._toolbarInitialized === true) {
            for (var i = this._toolbarItems.length; i--;) {
                this._toolbarItems[i].hide();
            }
        }
    };

    SimulationResultPlotterControl.prototype._removeToolbarItems = function () {

        if (this._toolbarInitialized === true) {
            for (var i = this._toolbarItems.length; i--;) {
                this._toolbarItems[i].destroy();
            }
        }
    };

    SimulationResultPlotterControl.prototype._initializeToolbar = function () {
        var self = this,
            toolBar = WebGMEGlobal.Toolbar;

        this._toolbarItems = [];

        this._toolbarItems.push(toolBar.addSeparator());

        /************** Go to hierarchical parent button ****************/
        this.$btnModelHierarchyUp = toolBar.addButton({
            title: 'Go to parent',
            icon: 'glyphicon glyphicon-circle-arrow-up',
            clickFn: function (/*data*/) {
                WebGMEGlobal.State.registerActiveObject(self._currentNodeParentId);
            }
        });
        this._toolbarItems.push(this.$btnModelHierarchyUp);
        this.$btnModelHierarchyUp.hide();

        /************** Checkbox example *******************/

        this.$cbShowConnection = toolBar.addCheckBox({
            title: 'Scattered plot',
            icon: 'glyphicon glyphicon-option-horizontal',
            checkChangedFn: function (data, checked) {
                self._scatteredOn = checked;

                console.log('scattered', self._scatteredOn);
                self._rebuildPlotData();

            }
        });
        this._toolbarItems.push(this.$cbShowConnection);

        this._toolbarInitialized = true;
    };

    return SimulationResultPlotterControl;
});
