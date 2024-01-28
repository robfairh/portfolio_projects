/*
This script hosts the queries for exploring data in MySQL.
Project idea from: https://www.youtube.com/watch?v=qfyynHBFOsM&list=PLUaB-1hjhk8FE_XZ87vPPSfHqb6OcM0cF&index=19

Convert data in .xlsx format into .csv:
* Download data from here: https://ourworldindata.org/covid-deaths
* Or to exactly follow along the video, go here: https://github.com/AlexTheAnalyst/PortfolioProjects/tree/main
* Download 'CovidDeaths.xlsx'
* Download 'CovidVaccinations.xlsx'
* Open files in LibreOffice and replace all empty cells with NULL
* Save as .csv
* This creates the files:
  * 'CovidDeaths.csv' (included in the repo)
  * 'CovidVaccinations.csv' (included in the repo)


Input data into database:
* pip install csvkit
* Create Table headers in sql:
  * csvsql --dialect mysql --snifflimit 100000 CovidDeaths.csv > CovidDeaths.sql
  * csvsql --dialect mysql --snifflimit 100000 CovidVaccinations.csv > CovidVaccinations.sql
* Manually change data type for date to VARCHAR
* sudo cp CovidDeaths.csv /var/lib/mysql-files/CovidDeaths.csv
* sudo cp CovidVaccinations.csv /var/lib/mysql-files/CovidVaccinations.csv

*/

-- Create and select database
CREATE DATABASE Covid;
USE Covid;

-- Create tables
-- Copy paste contents of 'CovidDeaths.sql' into mysql
-- Copy paste contents of 'CovidVaccinations.sql' into mysql

-- Load data into tables
LOAD DATA INFILE '/var/lib/mysql-files/CovidDeaths.csv'
INTO TABLE CovidDeaths
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA INFILE '/var/lib/mysql-files/CovidVaccinations.csv'
INTO TABLE CovidVaccinations
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Convert date from string format to date format
SELECT date FROM CovidDeaths LIMIT 5;
ALTER TABLE CovidDeaths ADD COLUMN ndate DATE AFTER date;
UPDATE CovidDeaths SET ndate = STR_TO_DATE(date, "%m/%d/%Y");
ALTER TABLE CovidDeaths DROP COLUMN date;
ALTER TABLE CovidDeaths CHANGE COLUMN ndate date DATE;

SELECT date FROM CovidVaccinations LIMIT 5;
ALTER TABLE CovidVaccinations ADD COLUMN ndate DATE AFTER date;
UPDATE CovidVaccinations SET ndate = STR_TO_DATE(date, "%m/%d/%Y");
ALTER TABLE CovidVaccinations DROP COLUMN date;
ALTER TABLE CovidVaccinations CHANGE COLUMN ndate date DATE;






Importing csv into sql:
* first create table, either manually or with the following:










-- Select Data that we are going to be using
SELECT location, date, total_cases, new_cases, total_deaths, population
FROM CovidDeaths
ORDER BY 1, 2
LIMIT 10;

-- Looking at Total Cases vs Total Deaths
-- DeathPercentage = likelihood of dying if contracting covid in a certain country
SELECT location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS DeathPercentage
FROM CovidDeaths
ORDER BY 1, 2
LIMIT 40;

-- Looking at Total Cases vs Total Deaths in Afghanistan: DeathPercentage is close to 4.3 %
SELECT location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS DeathPercentage
FROM CovidDeaths
WHERE location = 'Afghanistan'
ORDER BY 2 DESC
LIMIT 40;

-- Looking at Total Cases vs Total Deaths in the US: DeathPercentage is close to 1.8 %
SELECT location, date, total_cases, total_deaths, (total_deaths/total_cases)*100 AS DeathPercentage
FROM CovidDeaths
WHERE location LIKE '%states'
ORDER BY 2 DESC
LIMIT 40;

-- Get the average of that column for all countries and get worst countries: Yemen is the worst with 26.39 %
SELECT location, AVG(total_deaths/total_cases)*100 AS DeathPercentage
FROM CovidDeaths
GROUP BY location
HAVING DeathPercentage IS NOT NULL
ORDER BY DeathPercentage DESC
LIMIT 10;

-- Look at total cases vs population
-- Percentage of population got Covid
SELECT location, date, total_cases, population, (total_cases/population)*100 AS PopulationPercentage
FROM CovidDeaths
WHERE location LIKE '%states'
ORDER BY PopulationPercentage DESC
LIMIT 1;

-- See the countries with the worst numbers
-- Worst country: Andorra with 17.13% of the population getting covid
SELECT location, MAX(total_cases/population)*100 AS PopulationPercentage
FROM CovidDeaths
GROUP BY location
ORDER BY PopulationPercentage DESC
LIMIT 20;

-- Showing countries with highest death counts per population
SELECT location, MAX(total_deaths/population)*100 AS DeathPerPopulation
FROM CovidDeaths
GROUP BY location
ORDER BY DeathPerPopulation DESC
LIMIT 15;

-- how to see the data type of a column in the table
SELECT DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'CovidDeaths' AND COLUMN_NAME = 'total_deaths';

-- Showing countries with highest death counts per population
SELECT location, MAX(total_deaths) AS TotalDeathCount
FROM CovidDeaths
WHERE continent IS NOT NULL
GROUP BY location
ORDER BY TotalDeathCount DESC
LIMIT 15;

-- let's break things down by continent
SELECT continent, MAX(total_deaths) AS TotalDeathCount
FROM CovidDeaths
WHERE continent IS NOT NULL
GROUP BY continent
ORDER BY TotalDeathCount DESC;

-- GLOBAL NUMBERS
SELECT date, SUM(new_cases), SUM(new_deaths), SUM(new_deaths)/SUM(new_cases)*100
FROM CovidDeaths
WHERE Continent IS NOT NULL
GROUP BY DATE
ORDER BY 1, 2
LIMIT 40;

SELECT SUM(new_cases), SUM(new_deaths), SUM(new_deaths)/SUM(new_cases)*100
FROM CovidDeaths
WHERE Continent IS NOT NULL
ORDER BY 1, 2;


------- HERE
-- total population vs vaccinations
-- this creates a rolling summation
-- it is sort of numpy cumul
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations, SUM(vac.new_vaccinations) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM CovidDeaths AS dea
JOIN CovidVaccinations AS vac
    ON dea.location = vac.location
    AND dea.date = vac.date
WHERE dea.location LIKE '%States' AND vac.new_vaccinations IS NOT NULL
ORDER BY 2, 3
LIMIT 100;

-- We want to create a new table doing an operation based on RollingPeopleVaccinated
-- So we have 3 ways of doing it: CTE, TEMP table, or with a VIEW
-- USE CTE
WITH PopvsVacc (Continent, Location, Date, Population, RollingPeopleVaccinated) AS (
    SELECT dea.continent, dea.location, dea.date, dea.population, SUM(vac.new_vaccinations) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
    FROM CovidDeaths AS dea
    JOIN CovidVaccinations AS vac
        ON dea.location = vac.location
        AND dea.date = vac.date
    WHERE dea.location LIKE '%States' AND vac.new_vaccinations IS NOT NULL
    ORDER BY 2, 3
    LIMIT 100
)
SELECT *, (RollingPeopleVaccinated/population)*100 FROM PopvsVacc;

-- TEMP Table
DROP TABLE IF EXISTS PercentPopulationVaccinated;
CREATE TEMPORARY TABLE PercentPopulationVaccinated
(
continent nvarchar(255),
location nvarchar(255),
date datetime,
population numeric,
new_vaccinations numeric,
RollingPeopleVaccinated numeric
);

INSERT INTO PercentPopulationVaccinated
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations, SUM(vac.new_vaccinations) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM CovidDeaths AS dea
JOIN CovidVaccinations AS vac
    ON dea.location = vac.location
    AND dea.date = vac.date;

SELECT * FROM PercentPopulationVaccinated
WHERE location LIKE '%States' AND new_vaccinations IS NOT NULL
LIMIT 100;

-- Creating VIEW to store data for later visualizations
CREATE VIEW PercentPopulationVaccinated AS
SELECT dea.continent, dea.location, dea.date, dea.population, vac.new_vaccinations, SUM(vac.new_vaccinations) OVER (PARTITION BY dea.location ORDER BY dea.location, dea.date) AS RollingPeopleVaccinated
FROM CovidDeaths AS dea
JOIN CovidVaccinations AS vac
    ON dea.location = vac.location
    AND dea.date = vac.date
WHERE dea.continent IS NOT NULL;

SELECT * FROM PercentPopulationVaccinated LIMIT 100;

-- 2nd part of the portfolio project
SELECT SUM(new_cases) as total_cases, SUM(new_deaths) as total_deaths, SUM(new_deaths)/SUM(new_Cases)*100 as DeathPercentage
FROM CovidDeaths
WHERE continent IS NOT NULL
ORDER BY 1, 2

SELECT location, SUM(new_deaths) as TotalDeathCount
FROM CovidDeaths
WHERE continent IS NULL AND location NOT IN ('World', 'European Union', 'International')
GROUP BY location
ORDER BY TotalDeathCount DESC;

SELECT location, population, MAX(total_cases) as HighestInfectionCount, Max((total_cases/population))*100 as PercentPopulationInfected
FROM CovidDeaths
GROUP BY location, population
ORDER BY PercentPopulationInfected DESC;

SELECT Location, Population,date, MAX(total_cases) as HighestInfectionCount, Max((total_cases/population))*100 as PercentPopulationInfected
FROM CovidDeaths
GROUP BY Location, Population, date
ORDER BY PercentPopulationInfected DESC;