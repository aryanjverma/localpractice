# Monthly Billing Charges

# Monthly Billing Charges (Stripe-style)

Source note: The sources show the billing overview, subscription format, five-field change format, and chained-change example. Usage and tier schemas, numeric bounds, the addition sentinel, and the callable interface are authored practice details. The judged core task matches the visible source at about 90%.

Stripe Billing helps companies like Figma, Notion, and Slack bill their customers for subscriptions, plan changes, and usage. For example, a customer might pay a fixed monthly subscription fee, upgrade their plan partway through the month, and accrue usage-based charges for API calls or storage. At the end of the month, Stripe consolidates all of those items into a single invoice, which helps reduce transaction costs and keeps billing simple for both the merchant and their customers.

In this problem, you'll build a simplified version of that billing engine. You'll start by computing monthly totals from fixed subscriptions, then add prorated charges for mid-cycle plan changes, and finally layer in usage-based billing with both flat and tiered pricing. Each section builds directly on the previous one, so take time to structure your code in a way that's easy to extend.

## General Constraints and Assumptions

- All inputs are well-formed and valid.
- All monetary amounts are in USD cents (e.g. 1000 = $10.00).
- Billing cycles are exactly 30 days.
- Subscription IDs are unique across all subscriptions.
- A user may have multiple active subscriptions at the same time.
- A user may have usage-based billing without any subscriptions.
- Final charges are floored to the nearest cent right before charging the customer. (e.g. if a customer is to be charged $10.66666 for subscription_1 and $20.66666 for subscription_2, we expect the final charge to be floor(1066.666 + 2066.666) = 3133 (e.g. $31.33)
- Changes may not be provided in chronological order.
- The output should be a 2D string array where each inner array contains the user ID and their total charge as a string. e.g. ["user_1", "3500"].

## Function

`calculateMonthlyCharges(subscriptions: String[], changes: String[], pricing: String[], usage: String[]) → String[][]`

## Subscriptions

Each string in `subscriptions` has the format `user_id,subscription_id,monthly_cost`. These subscriptions are active from day 1. A user may have several subscriptions; subscription IDs are globally unique.

## Mid-month changes

Each string in `changes` has the format `user_id,old_subscription_id,new_subscription_id,new_monthly_cost,change_day`. On `change_day`, end the active old subscription and start the new subscription for the same user. Later changes may reference that new ID. Changes may arrive out of order.

Practice conventions: use `-` as `old_subscription_id` to add a subscription without replacing one. Otherwise the old ID must be active and belong to the given user. Every new ID is globally fresh, including IDs of retired subscriptions. Changes along one replacement chain have strictly increasing days; independent chains may change on the same day.

A version active from day `a` through day `b`, inclusive, contributes `monthly_cost * (b - a + 1) / 30` cents. A change on day `d` ends the old version on day `d - 1` and starts the new version on day `d`. The final version lasts through day 30.

## Flat and tiered usage pricing

Each string in `pricing` has the format `product_id,upper_bound,unit_price`. Rows for one product define marginal pricing tiers and may be unordered. Positive upper bounds are distinct cumulative quantities. Exactly one row per product has upper bound `-1`, meaning no upper limit.

After sorting finite bounds, the first tier prices units 1 through its upper bound, the next tier prices units after that bound through its own upper bound, and so on. The unlimited tier prices all remaining units. A product with only an unlimited tier has a flat per-unit price. Each unit is charged at the price of its own tier; the final tier's price does not apply retroactively to earlier units.

Each string in `usage` has the format `user_id,product_id,quantity`. Sum quantities separately for each user-product pair before applying that product's tiers. Different users do not share tier allowances. Usage charges are independent of subscription changes. A user may have usage without a subscription.

## Result

For each user mentioned in subscriptions, changes, or usage, add all subscription contributions and all usage charges, then floor the combined total once to the nearest cent. Do not round individual subscription segments or individual subscriptions. Include users whose total is zero.

Return a two-dimensional string array sorted lexicographically by user ID. Each row is `[user_id, total_charge_as_string]`, with no currency symbol or decimal point. Return an empty array when there are no users.

## Examples

### Example 1
subscriptions = ["user_1,sub_a,1000","user_1,sub_b,2500","user_2,sub_c,500","user_2,sub_d,3000","user_2,sub_e,1500","user_3,sub_f,2000"]
changes = []
pricing = []
usage = []
return = [["user_1","3500"],["user_2","5000"],["user_3","2000"]]

### Example 2
subscriptions = ["u1,s1,1000","u1,s2,2000"]
changes = ["u1,s1,s1_plus,2000,15"]
pricing = ["api,3,100","api,-1,50"]
usage = ["u1,api,2","u1,api,5"]
return = [["u1","4033"]]

### Example 3
subscriptions = ["u,s1,1000","u,s2,2000"]
changes = ["u,s2,s2_plus,3000,29", "u,s1,s1_plus,2000,29"]
pricing = []
usage = []
return = [["u","3133"]]

### Example 4
subscriptions = ["user_1,sub_a,1000","user_1,sub_b,2500","user_2,sub_c,500","user_3,sub_d,2000"]
changes = ["user_1,sub_a,sub_a_plus,1500,11","user_1,sub_a_plus,sub_a_pro,3000,21","user_2,sub_c,sub_c_premium,1200,16"]
pricing = []
usage = []
return = [["user_1","4333"],["user_2","850"],["user_3","2000"]]

## Constraints

- All input records are well-formed and valid.
- Identifiers are nonempty strings containing only ASCII letters, digits, and underscores; the literal `-` is reserved for the authored addition convention in `old_subscription_id`.
- Combined number of records across the four input arrays is at most 10^4. Every array may be empty.
- 1 ≤ change_day ≤ 30; 0 ≤ monthly_cost ≤ 10^9.
- 0 ≤ quantity ≤ 10^6; 0 ≤ unit_price ≤ 10^6.
- Every finite tier bound is between 1 and 10^10. Each product has distinct finite bounds and exactly one unlimited tier.
- Initial and new subscription IDs are globally unique. Replacements reference an active old ID owned by the same user. Days strictly increase along each replacement chain.
- All totals and intermediates scaled by 30 fit in a signed 64-bit integer.
