from io import BytesIO
import pandas as pd
import numpy as np

def interpret( all_df, df , days ):
 def parser(df,days,sname_is_last = False) : 
   df.dropna(subset = ["Salesman"] , inplace = True )
   df["party"] = df["Party Name"]
   df['Salesman']=df['Salesman'].apply(lambda x: x.split('-')[int(sname_is_last)])
   unfiltered =df.copy()
   filtered =df[df['In Days'] > days ]
   
   pivot_filtered = pd.pivot_table(filtered,index=['Salesman','Beat Name','party'],values=['O/S Amount','In Days'],aggfunc={'O/S Amount':np.sum,'In Days':np.max},margins=True)
   pivot_filtered_splitup = pd.pivot_table(filtered,index=['Salesman','Beat Name','party','Bill Number'],values=['O/S Amount','In Days'],aggfunc={'O/S Amount':np.sum,'In Days':np.max},margins=True)
   pivot_total_bills = pd.pivot_table(unfiltered,index=['Salesman','Beat Name','party'],values=['Bill Number'],aggfunc={'Bill Number':pd.Series.nunique},margins=True)
   pivot_filtered =pd.merge(pivot_total_bills,pivot_filtered,left_index=True,right_index=True)
   pivot_filtered=pivot_filtered[['Bill Number','In Days','O/S Amount']]
   return pivot_filtered, pivot_filtered_splitup
 
 all_df.to_excel("all_pending.xlsx")
 df.to_excel("outstanding.xlsx")
 outstanding_col_name = [ i for i in all_df.columns if "out" in i.lower() ][0]
 all_df = all_df.rename( columns = {"Salesman Name" : "Salesman",outstanding_col_name:"O/S Amount","Bill Ageing (In Days)":"In Days","Bill No" : "Bill Number"  })
 after_30_days = parser( all_df[ all_df['In Days'] <= 365 ] ,29, sname_is_last= True)[1]
 summary , detailed = parser(df,days)
 
 output = BytesIO()
 writer = pd.ExcelWriter(output, engine='xlsxwriter')
 summary.to_excel(writer, sheet_name='Summary')
 detailed.to_excel(writer, sheet_name='Detail')
 after_30_days.to_excel(writer, sheet_name='30 Days')
 writer.save()
 output.seek(0)

 return  output 





       





       

