#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri May 31 14:27:28 2019

@author: hanxinzhang
"""

import pickle
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from textwrap import wrap

# Constants preparation -------------------------------------------------------

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

monthWeeks = list(np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) / 7.)
monthsPartitions = np.cumsum([0.] + monthWeeks)
monthTicks = [(x + monthsPartitions[i+1]) / 2 for i, x in enumerate(monthsPartitions[:-1])]

with open('seasonality-web-app-data.bpkl3', 'rb') as f:
    dim3manifolds, dim2manifolds, seasonalityPlotData, condName = pickle.load(f)
    
# -----------------------------------------------------------------------------

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

available_algorithms = ['Principal Component Analysis (PCA)',
                        'Isomap',
                        'Locally Linear Embedding (LLE)',
                        'Modified Locally Linear Embedding (MLLE)',
                        'Local Tangent Space Alignment (LTSA)']

app.layout = html.Div([
        
    html.Div([
        html.H2('Seasonalities of diseases',
                style={
                    'width': '100%',
                    'bottom': '2rem',
                    'left': '4rem',
                    'position': 'relative',
                    'display': 'inline',
                    'font-size': '6.0rem'
                })
    ]),
        
    html.Div([
        html.Div([
            html.P('HOVER over a condition on the embedding graph to see its seasonality. '
                   'SCROLL to zoom in and out the embedding graph.'),
            html.P('HOLD the left mouse button and DRAG to rotate. '
                   'HOLD the right mouse button and DRAG to pan.'),
        ]),
        dcc.Dropdown(
            id='manifold algorithm',
            options=[{'label': i, 'value': i} for i in available_algorithms],
            value='Isomap',
            style={'width': '50rem'}
        ),
        dcc.RadioItems(
            id='dimensionality',
            options=[{'label': i, 'value': i} for i in ['2D', '3D']],
            value='3D',
            labelStyle={'display': 'inline-block'}
        )
    ],
    style={'width': '100%', 'display': 'inline-block', 'padding-left': '4rem'}),
    
    html.Div([
        dcc.Graph(
            id='manifold',
            hoverData={'points': [{'customdata': 0}]}
        )
    ],
    style={'display': 'inline-block',
           'width': '49%'}),    
    
    html.Div([
        dcc.Graph(id='seasonality'),
    ], style={'display': 'inline-block', 
              'width': '49%'}),
            
    html.Div([
        dcc.Graph(id='legend'),
    ], style={'display': 'inline-block', 
              'width': '100%'})

    
], style={'margin': '5rem'})
    
@app.callback(
    [dash.dependencies.Output('manifold', 'figure'), 
     dash.dependencies.Output('legend', 'figure')],
    [dash.dependencies.Input('manifold algorithm', 'value'),
     dash.dependencies.Input('dimensionality', 'value')])
def update_manifold(manifold_algorithm, dim):

    if dim == '2D':
        
        manifold_data, manifold_layout, legend_data, legend_layout = dim2manifolds[manifold_algorithm]
        
    else:
        
        manifold_data, manifold_layout, legend_data, legend_layout = dim3manifolds[manifold_algorithm]
        
    return ({'data': manifold_data, 'layout': manifold_layout}, 
            {'data': legend_data, 'layout': legend_layout})

        
    

@app.callback(
    dash.dependencies.Output('seasonality', 'figure'),
    [dash.dependencies.Input('manifold', 'hoverData')])
def update_seasonality(hoverData):
    
    condition_index = hoverData['points'][0]['customdata']
    hpd = seasonalityPlotData[condition_index]['hpd']
    mean = seasonalityPlotData[condition_index]['mean']
    thisCondName = '<br>'.join(wrap(condName[condition_index], 60))
    
    upper_bound = go.Scatter(
        y=hpd[:, 1],
        name='Upper bound',
        mode='lines',
        marker=dict(color="#444"),
        line=dict(width=0),
        fillcolor='rgba(68, 68, 68, 0.15)',
        fill='tonexty')
    
    trace = go.Scatter(
        y=mean,
        name='Mean',
        mode='lines',
        line=dict(color='rgb(31, 119, 180)'),
        fillcolor='rgba(68, 68, 68, 0.15)',
        fill='tonexty')
    
    lower_bound = go.Scatter(
        y=hpd[:, 0],
        name='Lower bound',
        marker=dict(color='rgba(68, 68, 68, 0.15)'),
        line=dict(width=0),
        mode='lines')

    data = [lower_bound, trace, upper_bound]
    
    fig = {'data': data, 
           'layout': go.Layout(
                   font={'family': 'Helvetica'},
                   yaxis=dict(title='DR seasonal fluctuation (95% C.I.)',
                              showexponent='last',
                              tickformat=',.0%'),
                   xaxis=dict(tickvals=monthTicks,
                              ticktext=MONTHS),
                   height=500,
                   title=thisCondName,
                   showlegend = False)}
                
    return fig
    
if __name__ == '__main__':
    app.run_server(debug=False)
    
    