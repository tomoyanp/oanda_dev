from scipy import stats



x = ["2017-10-01", "2017-10-02", "2017-10-03", "2017-10-04"]
x = [1,2,3,4]
y = [123.01, 123.02, 123.04, 123.05]
y = [1, 2, 3, 4]
y = [123.01, 123.02, 123.00, 123.15]


slope, intercept, r_value, _, _ = stats.linregress(x, y)
print slope
print intercept
print r_value
