import streamlit as st
import pandas as pd
import boto3
from dotenv import load_dotenv
import os
import io
from datetime import datetime

# Load environment variables
load_dotenv()

# AWS credentials
aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
bucket_name = os.getenv('BUCKET_NAME')

# Initialize S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key
)

def upload_to_s3(file, filename):
    try:
        s3.upload_fileobj(file, bucket_name, filename)
    except Exception as e:
        pass

import io
import boto3
import pandas as pd
from datetime import datetime

def df_upload_to_s3(df, file_name, bucket_name):
    """
    Uploads a Pandas DataFrame to an S3 bucket as a CSV file.
    
    :param df: Pandas DataFrame to upload
    :param file_name: Name of the file to be saved in S3
    :param bucket_name: Name of the S3 bucket
    """
    try:
        # Convert DataFrame to CSV in-memory
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        
        # Reset buffer position
        csv_buffer.seek(0)

        # Initialize S3 client
        s3_client = boto3.client('s3')

        # Upload to S3
        s3_client.upload_fileobj(csv_buffer, bucket_name, file_name)

        
    except Exception as e:
        pass



def po_aggregator(df):

    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)  # For CSV files
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)  # For Excel files
        else:
            raise ValueError("Unsupported file format") 
        
        
        df['Description']=df['Description'].str.split(', ')

        df.dropna(inplace=True,ignore_index=True)
        Colour_size_data={'Colour':[],"Size":[]}
        for i in range(len(df['Description'])):

            Colour_size_data['Colour'].append(df['Description'][i][1])
            Colour_size_data['Size'].append(df['Description'][i][2])
        
        df['Colour']=Colour_size_data['Colour']
        df['Size']=Colour_size_data['Size']
        pivotedMaster=df[['PO No','Colour','Size','Item Quantity','Plant','PACK']].pivot_table(index=['PO No','Colour','Plant','PACK'],columns=['Size'],values='Item Quantity',aggfunc='sum') 
        pivotedMaster.reset_index(inplace=True)
        pivotedMaster.fillna(0,inplace=True)

        pivotedMaster['Total']=pivotedMaster['XS']+pivotedMaster['S']+pivotedMaster['M']+pivotedMaster['L']+pivotedMaster['XL']+pivotedMaster['XXL']
        pivotedMaster.rename(columns={'Plant':'CODE'},inplace=True)

        try:
            pivotedMaster['Total']=pivotedMaster['Total'].astype(int)
            pivotedMaster['PO No']=pivotedMaster['PO No'].astype(int)
            pivotedMaster['XS']=pivotedMaster['XS'].astype(int)
            pivotedMaster['S']=pivotedMaster['S'].astype(int)
            pivotedMaster['M']=pivotedMaster['M'].astype(int)
            pivotedMaster['L']=pivotedMaster['L'].astype(int)
            pivotedMaster['XL']=pivotedMaster['XL'].astype(int)
            pivotedMaster['XXL']=pivotedMaster['XXL'].astype(int)
        except Exception as e:
            pass
        
        return pivotedMaster
    
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None


    

# Streamlit UI
st.title("🤖⚡⚙️PO-Aggregator⚡⚙️")
st.sidebar.write("Upload multiple Excel or CSV files to Aggregate the Po's")

# Initialize session state for uploaded files
if 'uploaded_files_status' not in st.session_state:
    st.session_state.uploaded_files_status = {}

uploaded_files = st.sidebar.file_uploader("Choose files", type=['csv', 'xlsx'], accept_multiple_files=True)

if uploaded_files:


    
    st.write("### Uploaded Files")
    for file in uploaded_files:

   
        with st.expander(f"📁 {file.name}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
          
                
                # Preview data
                try:
                    if file.name.endswith('.csv'):
                        df = pd.read_csv(file)
                        

                    else:
                        df = pd.read_excel(file)
                    st.markdown(f"Style: {file.name.split('.')[0]} \n\n Total Po's: {df['PO No'].nunique()} \n\n Total Order Quantity: {df['Item Quantity'].sum()}")
                    st.markdown(f"## Actual Data: {file.name.split('.')[0]}")
                    st.dataframe(df.head())
               
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
            
            with col2:
                # Individual upload button
                if st.button(f"Transform {file.name}", key=file.name):

                    with col1:
                        pivotedMaster=  po_aggregator(file)
                        st.markdown(f"## Transformed Data: {file.name.split('.')[0]}")
                        st.dataframe(pivotedMaster)

                    with col2:
                        
                        st.success(f"""Transformed Data:
                                  \n\n Style     : {file.name.split('.')[0]} 
                                  \n\n Total Po's: {pivotedMaster['PO No'].nunique()}
                                  \n\n Pack   : {pivotedMaster['PACK'].unique()}
                                  \n\n Colour : {pivotedMaster['Colour'].unique()}
                                  \n\n XS     : {pivotedMaster['XS'].sum()}
                                  \n\n S      : {pivotedMaster['S'].sum()}
                                  \n\n M      : {pivotedMaster['M'].sum()}
                                  \n\n L      : {pivotedMaster['L'].sum()}
                                  \n\n XL   : {pivotedMaster['XL'].sum()}
                                  \n\n XXL   : {pivotedMaster['XXL'].sum()}
                                  \n\n Total Order Quantity: {pivotedMaster['Total'].sum()}
                                  \n\n  """)
                        df_upload_to_s3(pivotedMaster, f"{datetime.now().strftime('%Y-%m-%d')}/Transformed/{file.name.split('.')[0]}_transformed_TOQ_{pivotedMaster['Total'].sum()}_TPOs_{len(pivotedMaster)}.csv", bucket_name)
                        st.download_button(

                            label="📥 Download CSV",
                            data=pivotedMaster.to_csv(),    
                            file_name=f"{file.name.split('.')[0]}_transformed_TOQ_{pivotedMaster['Total'].sum()}_TPOs_{len(pivotedMaster)}.csv",
                            mime='text/csv',

                        )
                        


        upload_to_s3(file, f"{datetime.now().strftime('%Y-%m-%d')}/Raw/{file.name}")
