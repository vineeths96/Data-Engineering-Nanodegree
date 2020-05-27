 ![Language](https://img.shields.io/badge/language-python--3.7-blue) [![Contributors][contributors-shield]][contributors-url] [![Forks][forks-shield]][forks-url] [![Stargazers][stars-shield]][stars-url] [![Issues][issues-shield]][issues-url] [![MIT License][license-shield]][license-url] [![LinkedIn][linkedin-shield]][linkedin-url]

<!-- PROJECT LOGO -->
<br />

<p align="center">
 <a href="https://github.com/vineeths96/Data-Engineering-Nanodegree">
 <img src="./images/logo.png" alt="Logo" width="250" height="125">
 </a>
 <h3 align="center">Twitter Sentiment Analysis</h3>
 <p align="center">
 Udacity Nanodegree Course Capstone Project
 <br />
 <a href=https://github.com/vineeths96/Data-Engineering-Nanodegree><strong>Explore the repository»</strong></a>
 <br />
 <br />
 </p>
</p>


> twitter, sentiment, s3, redshift, airflow, aws, data pipelines, data engineering, ETL 

<!-- ABOUT THE PROJECT -->

## About The Project

Twitter is one of the most popular social networking website in the world. Every second, on average, around 8,000 tweets are tweeted on Twitter, which corresponds to over 450,000 tweets sent per minute, 650 million tweets per day and around 250 billion tweets per year. As claimed by the official site, Twitter data is the most comprehensive source of live, public conversation worldwide.  Furthermore, Twitter allows developers to access their tweet data through their APIs that enable programmatic analysis of data in real-time or back to the first Tweet in 2006. This project aims to utilize the tweet data and combine the data with world happiness index data and earth surface temperature data and warehouse them on AWS. The Twitter data extraction could be limited to specific topics/hash-tags as per requirements which allows us to explore various domains.

### Project Description

In this project, we combine [Twitter](https://www.twitter.com) data, [World happiness index](https://www.kaggle.com/unsdsn/world-happiness) data and [Earth surface temperature data](https://www.kaggle.com/berkeleyearth/climate-change-earth-surface-temperature-data) data to explore whether there is any correlation between the above.  The Twitter data is dynamic and the other two dataset are static in nature. The general idea of this project is to extract Twitter data, analyze its sentiment and use the resulting data to gain insights with the other datasets. The entire process is orchestrated using Apache Airflow and is triggered automatically to run on daily schedule.

We choose one or more specific area of interests and extract the tweets related to those from Twitter. We can use the [tweepy](https://www.tweepy.org/) python library to access Twitter API and extract tweets data. We can set up the the Airflow to work in either of the two modes (by commenting/uncommenting line in the Airflow [DAG](./airflow/dag.py). 

|         Mode          |                        Specification                         |
| :-------------------: | :----------------------------------------------------------: |
| Historical Tweet mode | In this mode, the tweet data from the past days (from given date of beginning) are collected, organized into batches and uploaded. In this mode there are no time constraints, and hence basic preprocessing (such as removing unnecessary fields from tweet JSON) and sentiment extraction are done before uploading. |
| Real time Stream mode | In this mode, the tweet data from real time stream are collected and uploaded. Since we are streaming real time data, additional tasks such as preprocessing and sentiment extraction creates an overhead. Hence, the tweet stream are not processed and the tweet JSON data is uploaded as is. |

We use [AWS Comprehend](https://aws.amazon.com/comprehend/), which is a NLP service provided by AWS, to extract the sentiment from the tweet. As mentioned above, in [Historical Tweet mode](./airflow/search_tweets.py) we do the sentiment extraction before uploading and in [Real time Stream mode](./airflow/stream_tweets.py) we should setup our data pipelines to do the sentiment extraction after uploading. For the sake of this project, I have used `Historical Tweet mode` since real time streaming large amount of tweet data takes a significant amount of time. As of implementing this project, I ran this project on my local machine but deploying them on the cloud would be better due to its high reliability, availability and fault tolerance. We can use cloud services such as [AWS EC2](https://aws.amazon.com/ec2)  to deploy the tweet streaming (or even the whole project) for this purpose.

The tweet data is typically generated at high speeds, especially in the `Real time Stream mode`, and normal data uploading techniques often fails. We use [AWS Kinesis](https://aws.amazon.com/kinesis/), which is a real time streaming and analysis service provided by AWS, to ingest tweet data into [AWS S3](https://aws.amazon.com/s3). AWS S3 acts a data lake storing our static and dynamic data for further processing. We then stage the tweet data, temperature data and happiness index data on [AWS Redshift](https://aws.amazon.com/redshift/) and convert them to fact and dimensions tables (Star Schema) on AWS Redshift. This would allow us to answer insightful questions on the data and can be used for business analytics. 

Implementing the data stores and data warehouses on the cloud brings in lots of advantages. We can scale our resources vertically or horizontally as per our real time requirements with few clicks (or CLI commands). We can do the above much faster than implementing an on-premise resource with much less human working hours. We can also provide efficient access to our applications around the world by spreading our deployments to multiple regions.

**DAG Operations**

The Airflow DAG is set up to execute the following steps sequentially.

1. Start execution as per schedule
2. Create the AWS Redshift cluster
3. Upload static datasets to AWS S3
4. Stream tweet data to AWS Kinesis to ingest into AWS S3
5. Create tables on AWS Redshift
6. Stage the data from AWS S3 on AWS Redshift
7. Perform data quality check on the staging tables
8. Transform and load data into facts table 
9. Perform data quality check on the facts tables
10. Transform and load data into dimensional table 
11. Perform data quality check on the dimensional tables
12. Destroy the cluster
13. End execution

> NB: With slight modification to the code, we can remove the Step 4 which streams data from the DAG and manually run the `stream_tweets.py`. This would enable us to extract tweet from specific time of day when the script is run. 

> NB: Step 2 and Step 12 are only for demonstration purpose. By creating a separate DAG to create cluster which executes only once, we can deploy this model to run daily until manual interruption.

### Built With

* python
* Apache Airflow
* Amazon Web Services



## Database Schema Design

### Data Model ERD

The Star Database Schema (Fact and Dimension Schema) is used for data modeling in this ETL pipeline. There is one fact table containing all the metrics (facts) associated to each tweet and five dimensions tables, containing associated information such as user, source etc. This model enables to search the database schema with the minimum number of *SQL JOIN*s possible and enable fast read queries. 

![database](./images/database.png)

|        Table        |                         Description                          |
| :-----------------: | :----------------------------------------------------------: |
|   staging_tweets    |                 Staging table for tweet data                 |
|  staging_happiness  |         Staging table for world happiness index data         |
| staging_temperature |              Staging table for temperature data              |
|        users        | Dimension table containing user information derived from staging_tweets |
|       sources       | Dimension table containing sources (Android/iPhone) derived from staging_tweets |
|      happiness      | Dimension table containing happiness data derived from staging_happiness |
|     temperature     | Dimension table containing temperature data derived from staging_temperature |
|       tweets        | Fact table containing tweet information, happiness index and temperature derived from all three staging tables |

> NB: The data dictionary [DATADICT.md](DATADICT.md) contains a description of every attribute for all tables listed above.

Using this data model, we can finally answer questions regarding relationships between tweets, their sentiment, 
users, their location, happiness scores by country and variations in temperature by country.



## Apache Airflow Orchestration 

### DAG Structure

The DAG parameters are set according to the following :

- The DAG does not have dependencies on past runs
- DAG has schedule interval set to daily
- On failure, the task are retried 3 times
- Retries happen every 5 minutes
- Catchup is turned off
- Email are not sent on retry

The DAG dependency graph is given below.

![dag](./images/dag.png)



## What if ?

This section discusses strategies to deal with the following three key scenarios:

1. Data is increased 100x.  
2. Data pipeline is run on daily basis by 7 am every day.
3. Database needs to be accessed by 100+ users simultaneously.

#### 1. Data is increased 100x

In this project we have used scalable, fully managed cloud services to store and process our data throughout. As mentioned earlier, we can easily scale our resources vertically or horizontally with few clicks to tackle this scenario. Increased resources for AWS Redshift would allow us to load larger static datasets faster. For the increased volume of streaming tweet data, we could either upload the tweets in batches rather than individually or use multiple AWS Kinesis delivery streams to ingest data parallely.

#### 2. Data pipeline is run on a daily basis by 7 am every day

As the static datasets do not change on a daily basis, the major challenge here is to process the a day's amount of captured tweets in an acceptable time.  AWS Kinesis stores the data in AWS S3 partitioned by yearly/monthly/daily/hourly blocks. This makes it easy to run tasks in parallel DAGs with reduced data volume. Hence, the entire data could be processed within the stipulated time.

#### 3. Database needs to be accessed by 100+ users simultaneously

We are using cloud based services, which can be easily given access to the 100+ users. If a group of users work on a specific subset of data or have an expensive query, we can also explore creating duplicate tables for them (if possible).  



## Project structure

Files in this repository:

|  File / Folder   |                         Description                          |
| :--------------: | :----------------------------------------------------------: |
|     airflow      | Folder at the root of the project, where DAGs and associated python scripts are stored |
|     datasets     | Folder at the root of the project, where static datasets are stored |
|      images      |  Folder at the root of the project, where images are stored  |
|       sql        | Folder at the root of the project, where SQL commands are stored |
|    config.cfg    |                  Sample configuration file                   |
| requirements.txt |             Python environment requirements file             |
|     DATADICT     | Data Dictionary file with explanation of attributes of tables |
|    README.md     |                         Readme file                          |



<!-- GETTING STARTED -->

## Getting Started

Clone the repository into a local machine using

```sh
git clone https://github.com/vineeths96/Data-Engineering-Nanodegree
```

### Prerequisites

These are the prerequisites to run the program.

* python 3.7
* Twitter developer account and credentials
* Static datasets (from Kaggle)
* AWS IAM credentials
* AWS Kinesis Firehose
* AWS Comprehend
* AWS Redhift
* Apache Airflow
* python environment requirements: [requirements.txt](requirements.txt)

### How to run

Follow the steps to extract and load the data into the data model.

1. Set up Apache Airflow

2. Navigate to `Capstone Project` folder

3. Install requirements by

   ```sh
   pip install -r requirements.txt
   ```

4. Edit and fill in `config.cfg` as per requirements

5. Download the static datasets into [datasets](./datasets) directory

6. Trigger Airflow DAG ON

7. Verify the DAG execution by executing analytics tasks.



<!-- FUTURE WORK -->

## Future plan of work

Instead of using static datasets, I propose to use dynamic datasets. One particular scenario I have in mind is to use the [Twitter](https://www.twitter.com) tweet data and [Quandl](https://www.quandl.com) stock data to analyze the variation in the stock prize due to events such as Covid19.



<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE` for more information.



<!-- CONTACT -->

## Contact

Vineeth S - vs96codes@gmail.com

Project Link: [https://github.com/vineeths96/Data-Engineering-Nanodegree](https://github.com/vineeths96/Data-Engineering-Nanodegree)



<!-- ACKNOWLEDGEMENTS -->

## Acknowledgements

* [Stefan Langenbach](https://github.com/slangenbach)



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->

[contributors-shield]: https://img.shields.io/github/contributors/vineeths96/Data-Engineering-Nanodegree.svg?style=flat-square
[contributors-url]: https://github.com/vineeths96/Data-Engineering-Nanodegree/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/vineeths96/Data-Engineering-Nanodegree.svg?style=flat-square
[forks-url]: https://github.com/vineeths96/Data-Engineering-Nanodegree/network/members
[stars-shield]: https://img.shields.io/github/stars/vineeths96/Data-Engineering-Nanodegree.svg?style=flat-square
[stars-url]: https://github.com/vineeths96/Data-Engineering-Nanodegree/stargazers
[issues-shield]: https://img.shields.io/github/issues/vineeths96/Data-Engineering-Nanodegree.svg?style=flat-square
[issues-url]: https://github.com/vineeths96/Data-Engineering-Nanodegree/issues
[license-shield]: https://img.shields.io/badge/License-MIT-yellow.svg
[license-url]: https://github.com/vineeths96/Data-Engineering-Nanodegree/blob/master/LICENSE
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/vineeths
[product-screenshot]: images/screenshot.jpg