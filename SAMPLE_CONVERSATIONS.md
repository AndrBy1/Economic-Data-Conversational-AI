# Sample conversations

These describe expected responses, not a recorded live-FRED session. Numeric
answers depend on the loaded data; synthetic results must retain their label.

| User question | Calculated response |
| --- | --- |
| What is the latest reported U.S. GDP? | Latest available GDP in billions and its observation period. |
| How has U.S. GDP changed over the past 10 years? | First and last available GDP levels and percentage change. |
| What is the current Core CPI inflation rate? | Latest twelve-month percentage change and observation date. |
| How has Core CPI inflation changed over the past five years? | Initial and final YoY rates and actual available dates. |
| What is the relationship between GDP growth and Core CPI inflation? | Quarterly Pearson correlation, number of quarters, causation caveat, and chart. |
| Generate a visualization comparing GDP growth and Core CPI inflation over time. | Comparison chart in chat; dashboard offers PNG and CSV downloads. |
| Summarize the key economic trends observed in both datasets. | Growth and inflation endpoints, correlation, and chart. |

When Ollama is enabled and available, a separately labelled interpretation follows
the calculated response. Otherwise the app reports that Ollama is unavailable.
