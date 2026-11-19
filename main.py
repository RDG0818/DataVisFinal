import kagglehub

# Download latest version
path = kagglehub.dataset_download("yangkuangou/us-college-admissions-panel-ipeds-cds-2014-2024")

print("Path to dataset files:", path)