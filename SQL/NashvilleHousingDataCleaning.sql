/* 
This script hosts the queries for cleaning data in MySQL.
Project idea from: https://www.youtube.com/watch?v=8rO7ztF4NtU

Convert data in .xlsx format into .csv:
* To obtain the raw data go to: https://github.com/AlexTheAnalyst/PortfolioProjects/tree/main
* Download 'Nashville Housing Data for Data Cleaning.xlsx'
* Open file in LibreOffice and replace all empty cells with NULL
* Save as .csv
* Remove spaces from file name
* Open .csv file and manually change first column 'UniqueID ' to 'UniqueID'
* This creates the file: 'NashvilleHousingDataforDataCleaning.csv' that is included in this repo

Input data into database:
* pip install csvkit
* Create Table header in sql: csvsql --dialect mysql --snifflimit 100000 NashvilleHousingDataforDataCleaning.csv > NashvilleHeader.sql
* Manually change data types for SaleDate and SoldAsVacant to VARCHAR
* sudo cp NashvilleHousingDataforDataCleaning.csv /var/lib/mysql-files/

*/

-- Create and select database
CREATE DATABASE Nashville;
USE Nashville;

-- Create table
-- Copy paste contents of 'NashvilleHeader.sql' into mysql
ALTER TABLE NashvilleHousingDataforDataCleaning MODIFY COLUMN SalePrice VARCHAR(25);

-- Load data into table
LOAD DATA INFILE '/var/lib/mysql-files/NashvilleHousingDataforDataCleaning.csv'
INTO TABLE NashvilleHousingDataforDataCleaning
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Convert data type for SaleDate
Convert SaleDate from VARCHAR format to DATE format:

SELECT SaleDate FROM NashvilleHousingDataforDataCleaning LIMIT 5;
ALTER TABLE NashvilleHousingDataforDataCleaning ADD COLUMN nSaleDate DATE AFTER SaleDate;
UPDATE NashvilleHousingDataforDataCleaning SET nSaleDate = STR_TO_DATE(SaleDate, "%M %d, %Y");

SELECT nSaleDate FROM NashvilleHousingDataforDataCleaning LIMIT 5;
ALTER TABLE NashvilleHousingDataforDataCleaning DROP COLUMN SaleDate;
ALTER TABLE NashvilleHousingDataforDataCleaning CHANGE COLUMN nSaleDate SaleDate DATE;

-- Convert data type for SalePrice
Convert SalePrice from VARCHAR format to INT format:

SELECT SalePrice FROM NashvilleHousingDataforDataCleaning LIMIT 5;
ALTER TABLE NashvilleHousingDataforDataCleaning ADD COLUMN nSalePrice INT AFTER SalePrice;
UPDATE NashvilleHousingDataforDataCleaning SET nSalePrice = REPLACE(REPLACE(REPLACE(SalePrice, '$', ''), ',', ''), '"', '');

SELECT nSalePrice FROM NashvilleHousingDataforDataCleaning WHERE nSalePrice LIKE '%,%' LIMIT 5;
ALTER TABLE NashvilleHousingDataforDataCleaning DROP COLUMN SalePrice;
ALTER TABLE NashvilleHousingDataforDataCleaning CHANGE COLUMN nSalePrice SalePrice INT;

-- Rename table
ALTER TABLE NashvilleHousingDataforDataCleaning RENAME NashvilleHousing;



-- Cleaning the data
SELECT * FROM NashvilleHousing LIMIT 10;


-- 1) 
-- We need to populate PropertyAddress, as there are many entries that are NULL
-- And for that we will use ParcelID that it is not NULL
SELECT PropertyAddress FROM NashvilleHousing WHERE PropertyAddress IS NULL;
SELECT ParcelID FROM NashvilleHousing WHERE ParcelID IS NULL;

-- What we are doing here is using the fact that ParcelID is not NULL
-- and that usually, for the same ParcelID, the PropertyAddress is the same.
-- So we are joining the table to itself, and populate PropertAddress after making
-- sure that the line is not the same by using the UniqueID
SELECT a.ParcelID, a.PropertyAddress, b.ParcelID, b.PropertyAddress, IFNULL(a.PropertyAddress, b.PropertyAddress)
FROM NashvilleHousing AS a
JOIN NashvilleHousing AS b
    ON a.ParcelID = b.ParcelID
    AND a.UniqueID <> b.UniqueID
WHERE a.PropertyAddress IS NULL;

UPDATE NashvilleHousing AS a
JOIN NashvilleHousing AS b
    ON a.ParcelID = b.ParcelID
    AND a.UniqueID <> b.UniqueID
SET a.PropertyAddress = IFNULL(a.PropertyAddress, b.PropertyAddress)
WHERE a.PropertyAddress IS NULL;

-- Sanity check, to ensure that the NULLs in PropertyAddress are gone
SELECT PropertyAddress FROM NashvilleHousing WHERE PropertyAddress IS NULL;


-- 2)
-- Break out PropertyAddress into individual columns: Address, City, State
SELECT PropertyAddress FROM NashvilleHousing LIMIT 10;

SELECT SUBSTRING(PropertyAddress, 1, LOCATE(',', PropertyAddress)-1) AS Address,
       SUBSTRING(PropertyAddress, LOCATE(',', PropertyAddress)+1, LENGTH(PropertyAddress)) AS City
FROM NashvilleHousing LIMIT 10;

ALTER TABLE NashvilleHousing ADD COLUMN PropertySplitAddress VARCHAR(40) AFTER PropertyAddress;
UPDATE NashvilleHousing SET PropertySplitAddress = SUBSTRING(PropertyAddress, 1, LOCATE(',', PropertyAddress)-1);
SELECT PropertySplitAddress FROM NashvilleHousing LIMIT 5;

ALTER TABLE NashvilleHousing ADD COLUMN PropertySplitCity VARCHAR(40) AFTER PropertySplitAddress;
UPDATE NashvilleHousing SET PropertySplitCity = SUBSTRING(PropertyAddress, LOCATE(',', PropertyAddress)+1, LENGTH(PropertyAddress));
SELECT PropertySplitCity FROM NashvilleHousing LIMIT 5;


-- 3)
-- Break out OwnerAddress into individual columns: Address, City, State
SELECT OwnerAddress FROM NashvilleHousing LIMIT 5;

SELECT SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 1), ',', -1) AS Address,
       SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 2), ',', -1) AS City,
       SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 3), ',', -1) AS State
FROM NashvilleHousing LIMIT 5;

ALTER TABLE NashvilleHousing ADD COLUMN OwnerSplitAddress VARCHAR(40) AFTER OwnerAddress;
UPDATE NashvilleHousing SET OwnerSplitAddress = SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 1), ',', -1);
SELECT OwnerSplitAddress FROM NashvilleHousing LIMIT 5;

ALTER TABLE NashvilleHousing ADD COLUMN OwnerSplitCity VARCHAR(40) AFTER OwnerSplitAddress;
UPDATE NashvilleHousing SET OwnerSplitCity = SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 2), ',', -1);
SELECT OwnerSplitCity FROM NashvilleHousing LIMIT 5;

ALTER TABLE NashvilleHousing ADD COLUMN OwnerSplitState VARCHAR(40) AFTER OwnerSplitCity;
UPDATE NashvilleHousing SET OwnerSplitState = SUBSTRING_INDEX(SUBSTRING_INDEX(OwnerAddress, ',', 3), ',', -1);
SELECT OwnerSplitState FROM NashvilleHousing LIMIT 5;


-- 4)
-- Change Y/N to Yes/No in SoldAsVacant
SELECT DISTINCT(SoldAsVacant), COUNT(SoldAsVacant) FROM NashvilleHousing GROUP BY SoldAsVacant ORDER BY 2;

SELECT SoldAsVacant,
    CASE WHEN SoldAsVacant = 'Y' THEN 'Yes'
        WHEN SoldAsVacant = 'N' THEN 'No'
        ELSE SoldAsVacant
    END
FROM NashvilleHousing
LIMIT 5;

UPDATE NashvilleHousing
SET SoldAsVacant =
    CASE WHEN SoldAsVacant = 'Y' THEN 'Yes'
        WHEN SoldAsVacant = 'N' THEN 'No'
        ELSE SoldAsVacant
    END;


-- 5)
-- Remove duplicates: first we look at it, then, we delete
WITH RowNumCTE AS(
    SELECT *,
        ROW_NUMBER() OVER (
        PARTITION BY ParcelID, PropertyAddress, SalePrice, SaleDate, LegalReference ORDER BY UniqueID
        ) AS row_num
    FROM NashvilleHousing
)
SELECT * FROM RowNumCTE
WHERE row_num > 1
ORDER BY PropertyAddress;

WITH RowNumCTE AS(
    SELECT *,
        ROW_NUMBER() OVER (
        PARTITION BY ParcelID, PropertyAddress, SalePrice, SaleDate, LegalReference ORDER BY UniqueID
        ) AS row_num
    FROM NashvilleHousing
)
DELETE FROM NashvilleHousing
    USING NashvilleHousing
    JOIN RowNumCTE
    ON NashvilleHousing.UniqueID = RowNumCTE.UniqueID
WHERE RowNumCTE.row_num > 1;


-- 6)
-- Delete unused columns
ALTER TABLE NashvilleHousing DROP COLUMN OwnerAddress;
ALTER TABLE NashvilleHousing DROP COLUMN TaxDistrict;
ALTER TABLE NashvilleHousing DROP COLUMN PropertyAddress;
