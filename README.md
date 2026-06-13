# PySpark Job Recommendation System

This project is a simple, content-based job recommendation system built using Apache Spark (**PySpark**). It processes a scraped dataset of job postings and recommends jobs to users based on their skills, experience, education level, and salary expectations.

## Overview

The core of the recommendation engine relies on **TF-IDF (Term Frequency-Inverse Document Frequency)** and **Cosine Similarity**. It compares a user's inputted skills against the `job_requirements` of various job postings to find the closest matches.

## Features

- **Data Cleaning:** Automatically drops duplicate rows and handles incomplete scraped data (e.g., missing responsibilities).
- **Feature Engineering:** Extracts numerical minimum and maximum values for experience levels and salary ranges from text columns using Regular Expressions.
- **Categorical Encoding:** Standardizes and encodes education requirements into ordinal integers for easier filtering.
- **Pre-filtering:** Allows users to filter the job pool based on:
  - Job Type (e.g., Full-time, Internship)
  - Highest Education Level
  - Years of Experience
  - Salary Target
  - Job Category
- **Content-Based Filtering:** Tokenizes job requirements and user skills, computes TF-IDF vectors, and calculates a cosine similarity score to rank the best job matches for the user.

## Technologies Used

- **Python 3**
- **Apache Spark / PySpark** (Spark SQL for data manipulation, Spark MLlib for machine learning features)
- **Jupyter Notebook**

## Project Structure

- `preprocessing.ipynb`: The main Jupyter Notebook containing the entire pipeline—from loading and cleaning the data to running the recommendation algorithm.
- `dataset/glints_final_dataset_fast.csv`: The scraped dataset containing job postings (needs to be present in the `dataset` folder relative to the notebook). **You can download the dataset from [Hugging Face](https://huggingface.co/datasets/alflax77/glints-job-scraping).**

## How to Run

1. **Prerequisites:** 
   - Ensure you have **Java** installed (the notebook configures `JAVA_HOME` to `/usr/lib/jvm/java-21-openjdk-amd64`, you may need to adjust this based on your local setup).
   - Ensure you have `pyspark` and `jupyter` installed in your Python environment.
   - Install the **Jupyter** extension in Visual Studio Code.
   
2. **Open the Notebook:** Open the `preprocessing.ipynb` file inside VS Code. Select your installed Python environment as the Jupyter Kernel (usually in the top right corner).

3. **Execute Cells:** Run the cells sequentially from top to bottom. 

4. **Customize User Profile:** Look for the "user input" section in the notebook to test the recommendation engine with different skill sets and criteria:
   ```python
   user_skills = "Microsoft Excel, Data Entry, Administration, Problem Solving"
   user_years_of_experience = 1
   user_highest_education = "HIGH_SCHOOL"
   ```

## Future Improvements

- **Semantic Recommendations:** Upgrade from TF-IDF to Word Embeddings (like Word2Vec) to capture the semantic meaning of skills instead of relying on exact keyword matches.
- **Expanded Feature Set:** Include `job_responsibilities` and `job_title` in the text vectorization to provide a broader context for matching.
- **Soft Scoring:** Instead of strictly dropping jobs that don't meet the experience/education filters, apply penalty weights to their final similarity scores to provide a more holistic recommendation pool.
