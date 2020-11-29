from bokeh.models import Div


notes_div = Div(text="""
<h2>The Recognition Heuristic</h2>

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
<h2>References</h2>
<ol>
<li>Gigerenzer, Gerd, Peter M. Todd. <em>Simple Heuristics that make Us Smart.</em> Ebsco Publishing, Ipswich, 1999;2000;.</li>
</ol>
""",
width=800, height=150)
