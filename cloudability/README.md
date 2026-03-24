# Cloudability API

For reference see [Cloudability API](https://www.ibm.com/docs/en/cloudability-commercial/cloudability-standard/saas?topic=api-about-cloudability).

To access the API, you temporarily get a API Key or have a service account set up.

Set this API key locally

```bash
export CLOUDABILITY_KEY=<your key>
```


## Costs API

Reference [Cost Reporting Endpoint](https://www.ibm.com/docs/en/cloudability-commercial/cloudability-standard/saas?topic=api-cost-reporting-end-point)


### Example call returning GPU costs for yesterday

Dimensions:

* vendor (AWS, GCP etc)
* instance_type (the compute instance type per vendor)
* account_name (the name of the account in the vendor billing system)
* account_identifier (numerical id of above)
* category4 (Cost Center within RedHat)


```bash
# Store parameters in an array
params=(
  "start_date=beginning+of+last+day"
  "end_date=end%20of%20last%20day"
  "dimensions=vendor,instance_type,account_name,account_identifier,category4"
  "metrics=total_amortized_cost"
  "sort=total_amortized_costASC"
  "filters=transaction_type%3D%3Dusage"
  "filters=category9%3D%3Dai%20processors%20(gpu,%20accelerators,%20ml)"
)

# Join the array with ampersands
IFS='&'

curl "https://api.cloudability.com/v3/reporting/cost/run?${params[*]}" -u "$CLOUDABILITY_KEY:" \
| jq

```

Example output [sample_daily_costs](./sample_daily_costs.json).
