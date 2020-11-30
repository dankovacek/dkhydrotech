from os.path import join, dirname
import datetime

import pandas as pd
# from scipy.signal import savgol_filter

from bokeh.io import curdoc
from bokeh.layouts import row, column
from bokeh.models import (ColumnDataSource, DataRange1d, 
                         HoverTool, Slider, Div)
from bokeh.palettes import Blues4, brewer
from bokeh.plotting import figure

from content import title_div, notes_div, reference_div, p


def make_plot(source, title):
    plot = figure(plot_width=800, tools="", 
    toolbar_location=None, y_range=(0, 1),
    x_range=(0,N_objects_total))
    # plot.title.text = title

    # plot.line(x='N', y='f', color=Blues4[2], 
    # line_width=4, source=source)
    names = ['a_part', 'b_part', 'c_part']
    labels = ['P(RH)', 'P(G)', 'P(K)']
    plot.varea_stack(stackers=names, x='n_prop', color=brewer['Paired'][len(names)], legend_label=labels, source=source)
    plot.legend.items.reverse()

    plot.vline_stack(
        names,
        x="n_prop",
        line_width=5,
        color=brewer['Paired'][len(names)],
        source=source,
        alpha=0.,
    )

    # add hovertool
    plot.add_tools(HoverTool(show_arrow=True, line_policy='next', tooltips=[
        ('P(K)', '@c_part{0.000}'),
        ('P(G)', '@b_part{0.000}'), 
        ('P(RH)', '@a_part{0.000}'),
        ('n/N', '@n_prop{0.000}')
    ]))

    # fixed attributes
    plot.yaxis.axis_label = "f(n) (Expected Recall)"
    plot.xaxis.axis_label = "Proportion of Recognized Objects [n/N]"
    plot.axis.axis_label_text_font_style = "bold"
    plot.x_range = DataRange1d(range_padding=0.0)
    plot.grid.grid_line_alpha = 0.3

    return plot

def calculate_recall(N, n, a, b):
    a_part = 2 * (n / N) * (N - n) / (N - 1) * a
    b_part = (N - n)/ N * ((N - n - 1)/(N - 1)) / 2
    c_part = (n/N) * ((n - 1)/(N - 1)) * b 
    return a_part, b_part, c_part

def update_df(N, a, b):
    df = pd.DataFrame({'N': list(range(int(N + 1)))})
    df['n_prop'] = (df['N'] / N)
    df['a_part'], df['b_part'], df['c_part'] = zip(*df.apply(lambda row: calculate_recall(N, row['N'], a, b), axis=1))
    return ColumnDataSource(data=df)

def update_plot(attrname, old, new):
    a = alpha.value
    b = beta.value    

    title_var_string = f'N={N_objects_total}, α={a:.2f}, β={b:.2f}'
    plot.title.text = 'Expected Proportion of Correct Inferences ({})'.format(title_var_string)

    expected_recall = update_df(N_objects_total, a, b)

    source.data.update(expected_recall.data)



# city_select = Select(value=city, title='City', options=sorted(cities.keys()))
# distribution_select = Select(value=distribution, title='Distribution', options=['Discrete', 'Smoothed'])
N_objects_total = 1000
# n_objects_recognized = Slider(start=10, end=N_objects_total, value=N_objects_total / 2, step=1, title="n Recognized Objects")
alpha = Slider(start=0., end=1., value=0.5, step=0.01, title='α (Recognition Validity)')
beta = Slider(start=0., end=1., value=0.5, step=0.01, title='β (Knowledge Validity)')


source = update_df(N_objects_total, alpha.value, beta.value)

title_var_string = f'N={N_objects_total}, α={alpha.value:.2f}, β={beta.value:.2f}'
plot = make_plot(source, 'Expected Proportion of Correct Inferences ({})'.format(title_var_string))

alpha.on_change('value', update_plot)
beta.on_change('value', update_plot)

controls = column(alpha, beta)

main_row = row(plot, column(controls, notes_div))

layout = column(title_div, p, main_row, reference_div)

curdoc().add_root(layout)
curdoc().title = "Expected Recall by the Recognition Heuristic"