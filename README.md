# CONVERSATIONAL TAG AGENT FOR WEB CONTENT INTERACTION AND NAVIGATION

## INTRODUCTION/MOTIVATION
LLMs are increasingly becoming preferred option for accessing publicly available information through natural language interface. LLMs exceed expectation  excel in language tasks but they are parametric models whose responses are based on probability and hence prone to hallucination. Also, LLMs are purged of updated knowledge due to their knowledge cut off on the day they are trained. With this, LLM is not a good option for website visitors from countries around the world search around the over 19,000 url from both the main domain and sub domain of UTK website. In this project, we build a RAG system that will help UTK Website visitors to interact with information on UTK website through a web interface. To achieve this, we craw the utk.edu and scraped 19526 urls, build and retrieval system with the data so that the generator which is an LLM generate response only based on context provided from the knowledge base.
## PROJECT OBJECTIVE
There are over 19,000 pages from the main domain and sub-domain of the UTK website (utk.edu). Visitors from around the world scan through pages of this website every day looking from desired information. Most time, people need just a sentence to get the right information, but they had to scan through pages and read irrelevant content to get the information they need. The objective of this project is to build a RAG based chatbot through which website visitors can access information from the website without having to scan through different pages or reading irrelevant contents.
## PROJECT WORKFLOW
 - We write a script that takes a URL to the home page of a website and details of prefereed NOSQL Database (DynamoDB in our case), extract all URLs from the domain and subdomains (No link to external websites), extract all text data from the web pages and save in the chosed database. We used this script to extract texts from 19,526 URLs on UTK website
 - The we pulled the data from the database, converted each page into a seperate chunk, tokenize the chunk, embed with the Facebook DPR embedding model, index the vectors and store in pinecone database
 - We Build a FastAPI baclkend that fetches query, tokenize and embed the query, take that to the pinecone database, pick the top k index with the highest cosine similarity, build a more comprehensive propmt with the query and thr retrived knowledge, then take the prompt to the LLM to get generate response.
 - The response is passed to the user and stored in a Redis database. When the user sends another query, the query is combined with all previois query in the Redis database and sent for tokenization embedding and then to pinecone database to pick related index and repeat the same steps.
 - The frontend was build with React to prvide friendly interface for users
 - The backend (FastAPI) was containerized and deployed deployed on AWS EC2 Server
 - Frontend was also build and deployed to another EC2 Server
 - The deployment profess was automated using GitHub Action CI/CD Pipeline
## TOOLS USED IN THIS PROJECT
 - Programming Language - Python
 - Vector Embedding – Facebook DPR
 - Vector Database – Pinecone​
 - Backend – FastAPI
 - Frontend – React​
 - Web crawling and scrapping – Beautiful Soup and Playwright​
 - NoSQL Database – DynamoDB​
 - Workflow Orchestration – Prefect​
 - Cloud Serve - AWS EC2
 - Query Cache Storage - Redis
 - Rendering of Webpage - Nginx
 - COntainerization - Docker
 - CI/CD - Github Action
## WORKFLOW DIAGRAM
 - 
![image](https://github.com/user-attachments/assets/11cbe63c-3afc-4ea1-b6b3-aee478c916c8)

## REULT
The result for this project is an end to end RAG application we called UTKAsk
## APPLICATION LINKS
 - Frontend [here](http://3.144.96.138/)
 - Backend [here](http://3.143.23.19:8000/docs)
## How to Run The Project
 - Clone this github repo by running git clone https://github.com/joagada2/dse_697_fianl_project.git
   <pre> <code> https://github.com/joagada2/dse_697_fianl_project.git </code> </pre>
 - Create a DynamoDB Table and note the table's name
 - Enter the Table in the Webscraper script in the repo








 
 
 tion/Model Training
The model training process involved the neccessary proprocessing and experimentation, leading to the choice of the optimal model. The preprocessing steps include but not limited to diemsnionality reduction using different approach and arriving at different versions of dataset. Experimentaion involves fitting of 27 different algorithms to each of the versions of the dataset, out of which I selected the combination of the best-performing algorithm and best-performing dataset. This is how I arrived at ExtratreesClassifier applied to the balanced version of the full dataset as my optimal strategy. 
### Experiment Tracking
Experiment registry and model tracking were done using MLFlow.
### Workflow Orchestration
Workflow orchestration is necessary to enable continuous model re-training, batch inferencing and continous monitoring. All the workflows (preprocessing, model training, model evaluation, batch inferencing and continuous monitoring workfloes) were orchestrated using prefect. There are 3 different flows. The first contain all tasks from data preprocessing, model training to model evaluation. The second flow contains all tasks for batch inferencing while the third flow contains all tasks for continuous monitoring of model in production. All the workflow can either be triggered to run manually or automatically at pre-determined time interval.
### Model Serving
The model was wrapped in a FastAPI
### Remote Hosting of API
The FastAPI was deployed to AWS EC2. To access the API through the IP address, click [here](http://18.222.206.16:8000/docs#/default/predict_post_predict_post)

### Continous Integration and Continous Deployment (CI/CD)
I configured continuous integration and continuous deployment workflow for the project using GitHub Action. All the process of pusing the repository to AWS ECR and deploying the API to AWS EC2 were automated using Github Action CI/CD pipeline. 
### Offline Inferencing
Batch inferencing pipeline was also setup using Prefect. The pipeline searches through a an input folder at specified interval, picks any CSV file in the folder, preprocess the data, and use the model to assign label to the data. The confidence level for the prediction is also attached. After that, the pipeline deletes the original input from the input folder and sends the labeled dataset to an output folder.
### Model Monitoring/Full Stack Observability
Model inputs, outputs and metrics are being monitored continously for data drift, concept drift and performance decay. WhyLabs was used for this purpose.
### Other Automation
As seen earlier, all the worflows are automated meaning that there will be continuous update of the model without human intervention. Also, the CI/CD pipeline ensures automated pushing of updates to relevant AWS services (ECR and EC2). However, there is the need to also automate the pushing of updates from local repository to remote (github) repository. This was also automated with a bash script and a microsoft task that runs the script to automatically push update from local to remote repository at interval. With this, all steps have been fully automated.
### Project Versioning
Git was used for project version control
## USING THE PROJECT
The following steps can be followed to clone and run the project
 -   Clone project by running running the following command from git bash or command line:
```bash
git clone https://github.com/joagada2/mi_fatality_prediction.git
```
 -   Create a python 3.10 virtual environment and install requirements.txt including prefect 3.1.8, mlflow 2.19.0 and whylogs 1.6.4
 -   Change directory to the project by running the following command from your command line: cd mi_fatality_prediction (type cd mi and use shift + tab to autocomplete)
 -  To use the API, run the following command from your command line: python app/main.py
 -  To run the re-training pipeline, run the following command from your command line, from root directory, run cd src/prefect_orchestration and run python training_tasks.py. This will deploy the code to prefect server. Run prefect server start to start the ui and access the ui on port 4200 by clicking [here](http://localhost:4200).
 -  To run/start the batch inferencing code, from project root directory, cd to the script by running cd batch inferencing and run python batch_inf_script.py to upload the code to prefect server and run tasks every seconds
 -  To run/start the whylabs continuous monitoring script, from root directory, run cd src/whylab_monitoring and run python monitoring_script.py. This will also deploy the code to prefect server and run successfully.
 -  Note the crone configuration if for the flows to run every second. This configuration can be changed to run the code at any interval of choice
 -  Note that ETL pipeline by data engineer is expected to suppy the data for re-training, batch inferencing and monitoring. The actual crone configuration should depend on how often new data are available

 ## TOOLS/SKILLS USED IN THIS PROJECT
  - Python (Pandas, matplotlib, seaborn, scikitlearn etc)
  - Lazypredict - for experimentation
  - ExtratreesClassifiers - for model training
  - MLFlow - Experiment registry/tracking
  - FastAPI - Model Serving
  - AWS EC2 - API deployment
  - AWS ECR - Repository management on AWS
  - GitHub/GitHub Action - Code hosting and CI/CD pipeline
  - WhyLabs - Continous monitoring of model in production
  - Prefect - For workflow orchestration
  - Git - For project version control
  - 
  - etc



