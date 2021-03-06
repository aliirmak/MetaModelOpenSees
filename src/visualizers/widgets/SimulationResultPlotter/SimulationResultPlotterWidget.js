/*globals define, WebGMEGlobal*/

/**
 * Generated by VisualizerGenerator 1.7.0 from webgme on Mon Nov 26 2018 16:35:30 GMT-0600 (Central Standard Time).
 */

define([
    './plotly-latest.min',
    'text!./SimulationResultPlotter.html',
    'css!./styles/SimulationResultPlotterWidget.css'
], function (Plotly, SimulationResultPlotterHTML) {
    'use strict';

    var SimulationResultPlotterWidget,
        WIDGET_CLASS = 'simulation-result-plotter';

    SimulationResultPlotterWidget = function (logger, container) {
        this._logger = logger.fork('Widget');

        this._el = container;

        this.nodes = {};
        this._initialize();

        this._logger.debug('ctor finished');
    };

    SimulationResultPlotterWidget.prototype._initialize = function () {
        var width = this._el.width(),
            height = this._el.height(),
            self = this;

        // set widget class
        this._el.addClass(WIDGET_CLASS);
        this._plotEl = $(SimulationResultPlotterHTML);
        this._plotEl.width(width);
        this._plotEl.height(height);

        // Create a dummy header
        // this._el.append('<h3>SimulationResultPlotter Events:</h3>');
        this._el.append(this._plotEl);
    };

    SimulationResultPlotterWidget.prototype.onWidgetContainerResize = function (width, height) {
        this._plotEl.width(width);
        this._plotEl.height(height);
        if (this._plotExists) {
            Plotly.relayout('plotContainer', {
                width: width,
                height: height
            });
        }
    };

    SimulationResultPlotterWidget.prototype.initPlot = function (data) {
        this._plotExists = true;
        if (data) {
            Plotly.react('plotContainer', data, {
                width: this._plotEl.width(),
                height: this._plotEl.height(),
                margin: {t: 20, b: 20, l: 20},
                hovermode: 'closest'
            });
        } else {
            Plotly.purge('plotContainer');
        }
    };

    /* * * * * * * * Visualizer life cycle callbacks * * * * * * * */
    SimulationResultPlotterWidget.prototype.destroy = function () {
    };

    SimulationResultPlotterWidget.prototype.onActivate = function () {
        this._logger.debug('SimulationResultPlotterWidget has been activated');
    };

    SimulationResultPlotterWidget.prototype.onDeactivate = function () {
        this._logger.debug('SimulationResultPlotterWidget has been deactivated');
    };

    return SimulationResultPlotterWidget;
});
