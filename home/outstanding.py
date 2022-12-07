from io import BytesIO
import pandas as pd
import numpy as np
def interpret(df , days ):
 df = df.dropna(subset = ["Salesman"])
 df["party"] = df["Party Name"]
 df['Salesman']=df['Salesman'].apply(lambda x: x.split('-')[0])
 unfiltered =df.copy()
 filtered =df[df['In Days'] > days ]
 pivot_filtered = pd.pivot_table(filtered,index=['Salesman','Beat Name','party'],values=['O/S Amount','In Days'],aggfunc={'O/S Amount':np.sum,'In Days':np.max},margins=True)
 pivot_filtered_splitup = pd.pivot_table(filtered,index=['Salesman','Beat Name','party','Bill Number'],values=['O/S Amount','In Days'],aggfunc={'O/S Amount':np.sum,'In Days':np.max},margins=True)
 pivot_total_bills = pd.pivot_table(unfiltered,index=['Salesman','Beat Name','party'],values=['Bill Number'],aggfunc={'Bill Number':pd.Series.nunique},margins=True)
 pivot_filtered =pd.merge(pivot_total_bills,pivot_filtered,left_index=True,right_index=True)
 pivot_filtered=pivot_filtered[['Bill Number','In Days','O/S Amount']]
 
 output = BytesIO()
 writer = pd.ExcelWriter(output, engine='xlsxwriter')
 pivot_filtered.to_excel(writer, sheet_name='Summary')
 pivot_filtered_splitup.to_excel(writer, sheet_name='Detail')
 writer.save()
 output.seek(0)

 return  output 





       





       

