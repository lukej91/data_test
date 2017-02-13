
import numpy as np
import pandas as pd
import datetime

class apple1(object):

  def __init__(self):
    self.df = pd.read_csv('data.csv',
			names=['restaurant','product','quantity','price','currency','ordered_at'], 
			parse_dates=[5])

    self.df['value'] = self.df['quantity'] * self.df['price']
    self.df['year'] = self.df['ordered_at'].dt.year
    self.df['month'] = self.df['ordered_at'].dt.month

    # Extract max, min, mean, std, total for each month
    self.industry_summary = self.df.groupby(by=['currency','year','month']).agg({
			'quantity': {
				'count': len,
				'total': sum,
				'maximum': np.max,
				'minimum': np.min,
				'mean': np.mean,
				'std': np.std
			},
			'price': {
				'maximum': np.max,
				'minimum': np.min,
				'%change': lambda x: 100*(max(x) - min(x))/np.mean(x),
				'mean': np.mean,
				'std': np.std
			},
			'value': {
				'total': sum,
				'maximum': np.max,
				'minimum': np.min,
				'mean': np.mean,
				'std': np.std
			}})

    # Extract max, min, mean, std, total for each restaurant, each month
    self.restaurant_summary = self.df.groupby(by=['currency','restaurant','year','month']).agg({
			'quantity': {
				'count': len,
				'total': sum,
				'maximum': np.max,
				'minimum': np.min,
				'mean': np.mean,
				'std': np.std
			},
			'price': {
				'maximum': np.max,
				'minimum': np.min,
				'%change': lambda x: 100*(max(x) - min(x))/np.mean(x),
				'mean': np.mean,
				'std': np.std
			},
			'value': {
				'total': sum,
				'maximum': np.max,
				'minimum': np.min,
				'mean': np.mean,
				'std': np.std
			}})

  def value_month_to_month(self, month=None):
    # Use value portion of summary
    restaurant_value = self.restaurant_summary['value'].copy()
    industry_value = self.industry_summary['value'].copy()

    # Monthly changes in restaurant total order value and mean order value
    restaurant_value[['shifted_mean','shifted_total']] = restaurant_value.groupby(level=0)[['mean','total']].shift()
    restaurant_value['%change_mean'] = 100*(restaurant_value['mean']-restaurant_value['shifted_mean'])/restaurant_value['shifted_mean']
    restaurant_value['%change_total'] = 100*(restaurant_value['total']-restaurant_value['shifted_total'])/restaurant_value['shifted_total']

    # Monthly changes in industry total order value and mean order value
    industry_value[['shifted_mean','shifted_total']] = industry_value[['mean','total']].shift()
    industry_value['%change_mean'] = 100*(industry_value['mean']-industry_value['shifted_mean'])/industry_value['shifted_mean']
    industry_value['%change_total'] = 100*(industry_value['total']-industry_value['shifted_total'])/industry_value['shifted_total']

    # Merge industry stats with restaurant stats for comparison
    value = pd.merge(restaurant_value.reset_index(), industry_value[['%change_mean','%change_total']].reset_index(),
			on=['currency','year','month'],
			how='left',
			suffixes=['_res','_ind']).set_index(['currency','restaurant','year','month'])

    # Drop any ununsed columns
    value.drop(['maximum','minimum','std','shifted_mean','shifted_total'], axis=1, inplace=True)

    # Calculate normalised %change for each restaurant
    value['normalised_%change_mean'] = value['%change_mean_res'] - value['%change_mean_ind']
    value['normalised_%change_total'] = value['%change_total_res'] - value['%change_total_ind']

    if month:
      # Select month to analyse
      month_value = value.iloc[value.index.get_level_values('month') == month]
      # Show worst performers
      print(month_value[['mean','%change_mean_ind','%change_mean_res']].sort_values(by=['%change_mean_res']).head(10))
      print(month_value[['total','%change_total_ind','%change_total_res']].sort_values(by=['%change_total_res']).head(10))

    # Define current year and month
    current_month = datetime.date.today().month
    current_year = datetime.date.today().year

    # Extract stats from 1 month ago
    month_1 = value.xs((current_year,current_month-1), level=[2,3])

    # Extract only restaurants that have shown underperformance to industry average
    month_1 = month_1['normalised_%change_total'].loc[month_1['normalised_%change_total'] < 0]

    # Extract stats from this month
    month_2 = value.xs((current_year,current_month), level=[2,3])

    # Extract only restaurants that have shown underperformance to industry average
    month_2 = month_2['normalised_%change_total'].loc[month_2['normalised_%change_total'] < 0]

    # Keep only those showing continued underperformace
    caution = pd.merge(month_1.reset_index(), month_2.reset_index(),
			on=['currency','restaurant'],
			how='inner',
			suffixes=['-1','-2']).set_index(['currency','restaurant'])

    # These restaurants are showing continued underperformance and so may be more likely to go out of business
    caution['%bimonthly_contraction'] = (caution['normalised_%change_total-1'] + caution['normalised_%change_total-2'])/2
    # Order results by worst effected
    caution.sort_values(by='%bimonthly_contraction', ascending=True, inplace=True)

    # Show results for South of Ireland
    print('\nBadly performing restaurants over past two months in the south of Ireland:\n')
    print(caution.iloc[caution.index.get_level_values('currency') == 'EUR'].head())
    # Show results for South of Ireland
    print('\nBadly performing restaurants over past two months in the north of Ireland:\n')
    print(caution.iloc[caution.index.get_level_values('currency') == 'GBP'].head())

# Native console display setting
pd.set_option('display.width',180)

# Create object and run month to month value analysis
analysis = apple1()
analysis.value_month_to_month()
