import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import (Input, Output)

import pandas as pd
import plotly.graph_objs as go

from PageDesign import (colors_useful, tracking_realtime, insightful_history)
from TrackingFlow import (GrabOccurrenceData, GrabMagnitudes, GrabSpecificArea)
from TrackingReport import (GrabFeltReport, GrabAlertReport, GrabTsunamiReport)
from GraphPlotting import (PlotDensityMap, PlotScatterMap, LayoutDensity, LayoutScatter, LayoutScatterFrames)
from CountryHistoryProne import (GrabContentPerYear, GetDataYearValue, GetCountryDataByYear)

external_scripts = ['https://www.google-analytics.com/analytics.js']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

default_colorscale = [
	[0, '#a303b9'],	[0.25, '#ea6402'],[0.5, '#fa73a0'],	
	[0.75, '#f03b20'], [1, '#bd0026'],
]
radius_multiplier = {'inner' : 1.5, 'outer' : 3}

app = dash.Dash(__name__,
	external_scripts=external_scripts,
	external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True

app.layout = html.Div([
	dcc.Tabs(id='tabs', children=[
		dcc.Tab(label='Live Tracking', children=[
			tracking_realtime
		], className='custom-tab', selected_className='custom-tab--selected'),
		dcc.Tab(label='History (1965 - 2016)', children=[
			insightful_history
		], className='custom-tab', selected_className='custom-tab--selected')
	]),
	html.Div([])
])

#<magnitude_list>
@app.callback(
	Output('magnitude-range', 'options'), 
	[Input('past-occurrence', 'value'), Input('output-update', 'n_intervals')]
)
def update_mag_range(past_occurrence, n_intervals):
	mag_range = GrabMagnitudes(past_occurrence)
	mag_range.reverse()
	return [{'label' : m, 'value' : m} for m in mag_range]
#</magnitude_list>

#<area_list>
@app.callback(
	Output('area-list', 'options'), 
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('output-update', 'n_intervals')]
)
def update_area_list(past_occurrence, mag_value, n_intervals):
	area_list = GrabSpecificArea(past_occurrence, mag_value)
	area_list.insert(0, 'Worldwide')
	return [{'label' : area, 'value' : area} for area in area_list]
#</area_list>

#<comment_this_while deploying>
# @app.callback(
# 	Output('magnitude-range', 'value'),
# 	[Input('past-occurrence', 'value'), Input('magnitude-range', 'options'), 
# 		Input('output-update', 'n_intervals')]
# )
# def set_magnitude_value(past_occurrence, options, n_intervals):
# 	if past_occurrence == 'all_hour':
# 		return options[-1]['value']
# 	return options[-3]['value']

# @app.callback(
# 	Output('area-list', 'value'), 
# 	[Input('area-list', 'options'), Input('output-update', 'n_intervals')]
# )
# def set_area_value(options, n_intervals):
# 	return options[0]['value']
#</comment_this_while deploying>

#<title_largest_quake>
@app.callback(
	Output('largest-quake', 'children'), 
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('area-list', 'value'), Input('output-update', 'n_intervals')]
)
def update_largest_quake(past_occurrence, mag_value, specific_area, n_intervals):
	eqdf = GrabOccurrenceData(past_occurrence, mag_value)

	try:
		if specific_area == 'Worldwide':
			eqdf = eqdf
		else:
			eqdf = eqdf[eqdf['place'].str.contains(str(specific_area.split(' - ')[0]))]

		lq_mq = eqdf[['mag', 'place']]
		l_quake = lq_mq[lq_mq['mag'] >= lq_mq['mag'].max()]
		result = 'M ' + str(l_quake['mag'].to_list()[0]) + ' -- ' + l_quake['place'].to_list()[0]
		return html.Div([html.H3(result)])
	except Exception as e:
		return ''
#</title_largest_quake>

#<seismic_felt_report>
@app.callback(
	Output('felt-reports', 'children'),
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('area-list', 'value'), Input('output-update', 'n_intervals')]
)
def update_felt_report(past_occurrence, mag_value, specific_area, n_intervals):
	f_locations, f_reports = GrabFeltReport(past_occurrence, mag_value, specific_area)
	if len(f_locations) == 0 == len(f_reports):
		return html.Div([
			html.P('Everything seems clear ...', 
				style={'textAlign' : 'center', 'margin-top' : 40, 'margin-bottom' : 40})
		])
	report_list = []
	for f in range(len(f_reports)):
		report_list.append(
			html.Div([
				html.P('Location: ' + str(f_locations[f]), style={'color' : colors_useful['loc_color']}),
				html.P('Felt: ' + str(f_reports[f]), style={'color' : colors_useful['report_color']}),
				html.P('-'*25)
			])
		)
	return report_list
#</seismic_felt_report>

#<seismic_alert_report>
@app.callback(
	Output('alert-reports', 'children'), 
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('area-list', 'value'), Input('output-update', 'n_intervals')]
)
def update_alert_report(past_occurrence, mag_value, specific_area, n_intervals):
	a_locations, a_reports = GrabAlertReport(past_occurrence, mag_value, specific_area)
	if len(a_locations) == 0 == len(a_reports):
		return html.Div([
			html.P('Everything seems clear ...', 
				style={'textAlign' : 'center', 'margin-top' : 40, 'margin-bottom' : 40})
		])
	report_list = []
	for a in range(len(a_reports)):
		report_list.append(
			html.Div([
				html.P(a_locations[a], style={'color' : a_reports[a]}),
				html.P('-'*25)
			])
		)
	return report_list
#</seismic_alert_report>

#<seismic_tsunami_report>
@app.callback(
	Output('tsunami-reports', 'children'),
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('area-list', 'value'), Input('output-update', 'n_intervals')]
)
def update_tsunami_report(past_occurrence, mag_value, specific_area, n_intervals):
	t_locations = GrabTsunamiReport(past_occurrence, mag_value, specific_area)
	if len(t_locations) == 0:
		return html.Div([
			html.P('Everything seems clear ...', 
				style={'textAlign' : 'center', 'margin-top' : 40, 'margin-bottom' : 40})
		])
	report_list = []
	for t in range(len(t_locations)):
		report_list.append(
			html.Div([
				html.P(t_locations[t], style={'color' : colors_useful['tsunami_color']}),
				html.P('-'*25)
			])
		)
	return report_list
#</seismic_tsunami_report>

#<density_scatter_mapbox>
@app.callback(
	Output('map-quakes', 'children'),
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('map-type', 'value'), Input('area-list', 'value'), 
		Input('output-update', 'n_intervals')],
)
def visualize_quakes(past_occurrence, mag_value, map_type, specific_area, n_intervals):
	try:
		eqdf = GrabOccurrenceData(past_occurrence, mag_value)
		if specific_area == 'Worldwide':
			eqdf = eqdf
			zoom = 1
			radius = 10
		else:
			eqdf = eqdf[eqdf['place'].str.contains(str(specific_area.split(' - ')[0]))]
			zoom = 3
			radius = 15

		latitudes = eqdf['latitude'].to_list()
		longitudes = eqdf['longitude'].to_list()
		magnitudes = eqdf['mag'].to_list()
		mags = [float(i) * radius_multiplier['outer'] for i in magnitudes]
		mags_info = ['Magnitude : ' + str(m) for m in magnitudes]
		depths = eqdf['depth'].to_list()
		deps_info = ['Depth : ' + str(d) for d in depths]
		places = eqdf['place'].to_list()

		center_lat = eqdf[eqdf['mag'] == eqdf['mag'].max()]['latitude'].to_list()[0]
		center_lon = eqdf[eqdf['mag'] == eqdf['mag'].max()]['longitude'].to_list()[0]

		if (map_type == 'Density Map'):
			map_trace = PlotDensityMap(latitudes, longitudes, magnitudes, radius, 'Electric')
			layout_map = LayoutDensity(600, 980, 'stamen-terrain', center_lat, center_lon, zoom)
			visualization = html.Div([
				dcc.Graph(
					id='density-map',
					figure={'data' : [map_trace], 'layout' : layout_map}
				),
			])
			return visualization

		if (map_type == 'Scatter Map'):
			quake_info = [places[i] + '<br>' + mags_info[i] + '<br>' + deps_info[i]
				for i in range(eqdf.shape[0])]
			map_trace = PlotScatterMap(latitudes, longitudes, mags, magnitudes, default_colorscale, quake_info)
			layout_map = LayoutScatter(600, 980, 'stamen-terrain', center_lat, center_lon, zoom)
			visualization = html.Div([
				dcc.Graph(
					id='scatter-map',
					figure={'data' : [map_trace], 'layout' : layout_map}
				),
			])
			return visualization
	except Exception as e:
		return html.Div([
			html.H6('Please select valid magnitude / region ...')
		], style={'margin-top' : 150, 'margin-bottom' : 150, 'margin-left' : 200})
#</density_scatter_mapbox>

#<earthquake_type_pie>
@app.callback(
	Output('pie-quake-type', 'children'), 
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('output-update', 'n_intervals')]
)
def category_pie_chart(past_occurrence, mag_value, n_intervals):
	eqdf = GrabOccurrenceData(past_occurrence, mag_value)
	qtype = eqdf['type'].value_counts().to_frame()
	qtype.reset_index(inplace=True)
	qtype.columns = ['type', 'count']
	labels = qtype['type'].to_list()
	values = qtype['count'].to_list()

	pie_type = go.Pie(labels=labels, values=values, hole=0.3, pull=0.03, 
		textposition='outside', rotation=100)
	pie_layout = go.Layout(title='Disaster type')

	pie_chart_type = html.Div([
		dcc.Graph(id='disaster-type', figure={'data' : [pie_type], 'layout' : pie_layout})
	])
	return pie_chart_type
#</earthquake_type_pie>

#<count_area_bar>
@app.callback(
	Output('area-count-plot', 'children'),
	[Input('past-occurrence', 'value'), Input('magnitude-range', 'value'), 
		Input('output-update', 'n_intervals')]
)
def count_area_plot(past_occurrence, mag_value, n_intervals):
	counts_area = GrabSpecificArea(past_occurrence, mag_value)

	areas_alone = []; count_vals = []
	for area in counts_area:
		area = area.split(' - ')
		areas_alone.append(area[0])
		count_vals.append(int(area[1]))

	area_counter = go.Bar(x=areas_alone, y=count_vals)
	repeat_layout = go.Layout(title='Worldwide - ' + str(past_occurrence))

	repetitive_areas = html.Div([
		dcc.Graph(id='area-repeat-list', figure={'data' : [area_counter], 'layout' : repeat_layout})
	])
	difficult_message = html.Div([
		html.P('Quite difficult to load the graph ...')
	], style={'margin-top' : 150, 'margin-bottom' : 50, 'textAlign' : 'center'})

	if past_occurrence == 'all_week' and mag_value < 3:
		return difficult_message
	if past_occurrence == 'all_week' and mag_value >= 3:
		return repetitive_areas
	return repetitive_areas
#</count_area_plot>

#<top_thirty_countries_occurrences_by_year>
@app.callback(
	Output('map-history', 'children'),
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def history_scatter_map(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	if risky_country.shape[0] > 0:
		lats = risky_country['Latitude'].to_list()
		lons = risky_country['Longitude'].to_list()
		magnitudes = risky_country['Magnitude'].to_list()
		mags_info = ['Magnitude : ' + str(m) for m in magnitudes]
		depths = risky_country['Depth'].to_list()
		deps_info = ['Depth : ' + str(d) for d in depths]
		places = risky_country['Place'].to_list()
		country_risky_info = [places[i] + '<br>' + mags_info[i] + '<br>' + deps_info[i] 
			for i in range(risky_country.shape[0])]

		center_lat = risky_country[risky_country['Magnitude'] <= risky_country['Magnitude'].min()]['Latitude'].to_list()[0]
		center_lon = risky_country[risky_country['Magnitude'] <= risky_country['Magnitude'].min()]['Longitude'].to_list()[0]

		country_map = PlotScatterMap(lats, lons, 10, magnitudes, default_colorscale, country_risky_info)
		country_layout = LayoutScatter(400, 1000, 'stamen-terrain', center_lat, center_lon, 2.5)
		result_country = html.Div([
			dcc.Graph(
				id='risky-country-result',
				figure={'data' : [country_map], 'layout' : country_layout}
			)
		], style={'margin-top' : 20, 'margin-left' : 10})
		return result_country
	return html.Div([
		html.H6('No Earthquakes found for {} in the year {}'.format(risky_code, year_value))
	], style={'margin-top' : 150, 'margin-bottom' : 150, 'margin-left' : 250})
#</top_thirty_countries_occurrences_by_year>

#<basic_statistics>
@app.callback(
	Output('res-total-occurrences', 'children'), [Input('top-thirty-risky', 'value')]
)
def result_total_occurrences(risky_code):
	dataq = pd.read_csv('quake_db_1965-2016.csv')
	risky_country = dataq[dataq['Place'].str.contains(risky_code)]
	risky_country = risky_country[['Date', 'Latitude', 'Longitude', 'Magnitude', 'Depth', 'Type', 'Place']]
	if risky_country.shape[0] == 0:
		res_total = 0
	else: res_total = risky_country.shape[0]
	return html.P(str(res_total))

@app.callback(
	Output('res-year-num', 'children'), [Input('year-slider', 'value')]
)
def update_year_value(year_value):
	return html.P('( {} ) : '.format(year_value))

@app.callback(
	Output('res-yearly-occ', 'children'), 
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def result_yearly_occurrences(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	return html.P(str(risky_country.shape[0]))

@app.callback(
	Output('res-high-mag', 'children'),
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def result_highest_mag(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	mag_high = risky_country['Magnitude'].max()
	return html.P(str(mag_high))

@app.callback(
	Output('high-mag-depth', 'children'),
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def result_highest_depth(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	if risky_country.shape[0] == 0: depth_high_mag = 0
	else:
		depth_high_mag = risky_country[risky_country['Magnitude'] >= risky_country['Magnitude'].max()]['Depth'].to_list()[0]
	return html.P(str(depth_high_mag))

@app.callback(
	Output('high-mag-type', 'children'),
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def result_high_mag_type(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	if risky_country.shape[0] == 0: res_type = 'None'
	else:
		res_type = risky_country[risky_country['Magnitude'] >= risky_country['Magnitude'].max()]['Type'].to_list()[0]
	return html.P(res_type)

@app.callback(
	Output('res-place', 'children'),
	[Input('top-thirty-risky', 'value'), Input('year-slider', 'value')]
)
def result_place_name(risky_code, year_value):
	risky_country = GetCountryDataByYear(risky_code, year_value)
	if risky_country.shape[0] == 0: res_place = 'Null'
	else:
		res_place = risky_country[risky_country['Magnitude'] >= risky_country['Magnitude'].max()]['Place'].to_list()[0]
	return html.H6(res_place)
#</basic_statistics>


if __name__ == '__main__':
	app.run_server(debug=True, dev_tools_props_check=False, dev_tools_ui=False)
	# app.run_server(debug=True)