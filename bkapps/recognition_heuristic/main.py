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


x_range = (-20,-10) # could be anything - e.g.(0,1)
y_range = (20,30)

formula_label = figure(x_range=x_range, y_range=y_range, width=900, height=100,
    toolbar_location=None)
formula_label.axis.visible = False
formula_label.outline_line_color = None

img_path = 'http://localhost:5006/recognition_heuristic/static/gigenrenzer_fn.jpg'
formula_label.image_url(url=[img_path],x=x_range[0],y=y_range[1],w=x_range[1]-x_range[0],h=y_range[1]-y_range[0])


title_div = Div(text="""
<h4> How Ignorance Makes Us Smart (Goldstein & Gigerenzer, 1999)</h4>
""",
width=1000, height=100)

notes_div = Div(text="""
<h4>The Recognition Heuristic</h4>

<em>If one of two objects is recognized, infer that the recognized object is more likely to be the correct answer.</em>

<p>
Given a two-alternative choice test, i.e.
<blockquote><em>What city has a larger population: (City A) or (City B)?</em></blockquote>
Where <em>City A</em> and <em>City B</em> are selected randomly from a sample of <strong>N</strong> cities, of which <strong>n</strong> are "recognizable"<sup>1</sup>.
</p>

<p>
<strong>Recognition Validity (α):</strong>The probability of a correct answer when <strong>one of two choices</strong> is recognized.  In other words, how well the probability of recognition correlates with the criterion.  i.e. people are more likely to have heard of cities with larger population<sup>2</sup>.
</p>

<p><strong>Knowledge Validity (β):</strong>The probability of getting a correct answer when <strong>both choices</strong> are recognized.  In other words, how well the content of recognition corresponds with the question being asked.</p>

<strong>Notes:</strong>
<ol>
<li>The meaning of <em>recognizable</em> is the crux of the argument.  Is recognition a belief in familiarity?  If one has visited Paris, France, does one "recognize" Paris, Ontario to any significant degree when facing the alternative of Pickle Lake, Ontario?  </li>
<li>The more one is steeped in the music of legendary Canadian folk musician Tom Connors, the more negative the correlation between recognition and population (α→0).</li>
</ol>
""", width=400)

reference_div = Div(text="""
<h4>References</h4>
<ol>
<li>Gigerenzer, Gerd, Peter M. Todd. <em>Simple Heuristics that make Us Smart.</em> Ebsco Publishing, Ipswich, 1999;2000;.</li>
</ol>
""",
width=800, height=150)


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
    main_plot.title.text = 'Expected Proportion of Correct Inferences ({})'.format(title_var_string)

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
main_plot = make_plot(source, 'Expected Proportion of Correct Inferences ({})'.format(title_var_string))

alpha.on_change('value', update_plot)
beta.on_change('value', update_plot)

controls = column(alpha, beta)

main_row = row(main_plot, column(controls, notes_div))

layout = column(title_div, formula_label, main_row, reference_div)

curdoc().add_root(layout)
curdoc().title = "Expected Recall by the Recognition Heuristic"