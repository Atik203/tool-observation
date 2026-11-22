# Glossary

| Word | Meaning |
|---|---|
| **prefix** | A real τ-bench conversation cut just after a tool observation. |
| **observation** | The tool result the agent sees (JSON or prose). |
| **V** | The verbatim JSON observation. It is the reference, not a severity level. |
| **s0** | Faithful prose paraphrase of V. The placebo. |
| **s1** | One non-critical field changed. Negative control. |
| **s2** | One decision-critical field changed to a plausible wrong value. |
| **s3** | A critical change plus a second contradiction. |
| **arm** | One of V, s0, s1, s2, s3. |
| **signature** | The tool name + arguments, or the action verb + decision slots. |
| **donor** | The model that produced the original conversation (gpt-4o or claude-3.5-sonnet). |
| **silent propagation** | The model repeats the wrong value without flagging it and without changing the action. |
| **recovery** | The first later step where the model returns to the reference decision (R1) or flags the problem (R2). |
| **censored** | Neither R1 nor R2 happened by step 4. |
