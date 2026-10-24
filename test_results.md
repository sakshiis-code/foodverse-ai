| Test case | Result | Notes |
|---|---|---|
| API root is online | PASS | HTTP 200 |
| Food: no input | PASS | HTTP 400 (expected 400) |
| Food: text only | PASS | HTTP 200 |
| Food: non-food image | PASS | HTTP 400: {'detail': 'This does not look like food or a drink'} |
| Food: tiny image | PASS | HTTP 400 (expected 400) |
| Food: wrong file type | PASS | HTTP 400 (expected 400) |
| Food: 11 MB file rejected | PASS | HTTP 413 (expected 413) |
| Freshness: image missing | PASS | HTTP 422 (expected 422) |
| Freshness: blank image | PASS | HTTP 400 |
| Hygiene: no file | PASS | HTTP 422 (expected 422) |
| Hygiene: non-kitchen image | PASS | HTTP 400 |
| Kitchen: empty input | PASS | HTTP 400 (expected 400) |
| Kitchen: text ingredients | PASS | HTTP 200 |
| Meal: fields missing | PASS | HTTP 422 (expected 422) |
| Meal: invalid age | PASS | HTTP 422 (expected 422) |
| Meal: calorie target correct | PASS | maintenance target = 2085 kcal (expected about 2085) |
| Meal: peanut allergy respected | PASS | no peanuts in dishes or ingredients |

**17/17 passed**
