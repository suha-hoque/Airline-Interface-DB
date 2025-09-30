

CREATE TABLE Airport (
    Airport_Code CHAR(3) PRIMARY KEY,
    Airport_Name VARCHAR(100) NOT NULL,
    City VARCHAR(100),
    Country VARCHAR(100),
    Number_of_Terminals INT,
    Airport_Type VARCHAR(50)
);

CREATE TABLE Airline (
    Airline_Name VARCHAR(100),  
    PRIMARY KEY (Airline_Name)  
);

CREATE TABLE Flight (
    Flight_Num INT,
    Departure_Date DATE,
    Departure_Time TIME,
    Arrival_Date DATE,
    Arrival_Time TIME,
    Base_Ticket_Price DECIMAL(10, 2),
    Flight_Status VARCHAR(50),
    Airline_Name VARCHAR(100),  
    Arrival_Code CHAR(3),
    Departure_Code CHAR(3),
    PRIMARY KEY (Flight_Num, Departure_Date, Departure_Time, Airline_Name), 
    FOREIGN KEY (Airline_Name) REFERENCES Airline(Airline_Name),  
    FOREIGN KEY (Arrival_Code) REFERENCES Airport(Airport_Code),  
    FOREIGN KEY (Departure_Code) REFERENCES Airport(Airport_Code)  
);

CREATE TABLE Operates (
    Airline_Name VARCHAR(100),
    Airport_Code CHAR(3),
    PRIMARY KEY (Airline_Name, Airport_Code),
    FOREIGN KEY (Airline_Name) REFERENCES Airline(Airline_Name),
    FOREIGN KEY (Airport_Code) REFERENCES Airport(Airport_Code)
);

CREATE TABLE Airplane (
    Airline_Name VARCHAR(100),  
    Airplane_ID INT,                     
    Number_of_Seats INT,
    Manufacturing_Company VARCHAR(100),
    Model_Num VARCHAR(50),
    Manufacturing_Date DATE,
    Age INT,
    -- Age INT AS (YEAR(CURRENT_DATE) - YEAR(Manufacturing_Date)),  
    PRIMARY KEY (Airline_Name, Airplane_ID),
    FOREIGN KEY (Airline_Name) REFERENCES Airline(Airline_Name)
);

-- CREATE UNIQUE INDEX idx_airplane_id ON Airplane(Airplane_ID);

CREATE TABLE Owns (
    Airline_Name VARCHAR(100),
    Airplane_ID INT,
    PRIMARY KEY (Airline_Name, Airplane_ID),
    FOREIGN KEY (Airline_Name, Airplane_ID) REFERENCES Airplane(Airline_Name, Airplane_ID)
);

CREATE TABLE Maintenance_Procedure (
    Airline_Name VARCHAR(100),
    Airplane_ID INT,
    Start_Date DATE,
    Start_Time TIME,
    End_Date DATE,
    End_Time TIME,
    PRIMARY KEY (Airline_Name, Airplane_ID, Start_Date, Start_Time, End_Date, End_Time),
    FOREIGN KEY (Airline_Name, Airplane_ID) REFERENCES Airplane(Airline_Name, Airplane_ID)
);

CREATE TABLE Goes_Through (
    Airplane_ID INT,
    Airline_Name VARCHAR(100),
    Start_Date DATE,
    Start_Time TIME,
    End_Date DATE,
    End_Time TIME,
    PRIMARY KEY (Airplane_ID, Airline_Name, Start_Date, Start_Time, End_Date, End_Time),
    FOREIGN KEY (Airline_Name, Airplane_ID) REFERENCES Airplane(Airline_Name, Airplane_ID),
    FOREIGN KEY (Airline_Name, Airplane_ID, Start_Date, Start_Time, End_Date, End_Time) 
        REFERENCES Maintenance_Procedure(Airline_Name, Airplane_ID, Start_Date, Start_Time, End_Date, End_Time)
);



CREATE TABLE Customer (
    Email VARCHAR(254) PRIMARY KEY,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Passcode VARCHAR(50),
    Building_Num INT,
    Street_Name VARCHAR(100),
    Apartment_Num INT,
    City VARCHAR(50),
    State VARCHAR(50),
    Zip_Code VARCHAR(10),
    Date_of_Birth DATE
);

CREATE TABLE Customer_Phone (
    Email VARCHAR(254), 
    Phone VARCHAR(15),
    PRIMARY KEY (Email, Phone),
    FOREIGN KEY (Email) REFERENCES Customer(Email)
);

CREATE TABLE Customer_Passport (
    Email VARCHAR(254),
    Passport_Number VARCHAR(20),
    Passport_Expiration DATE,
    Passport_Country VARCHAR(50),
    PRIMARY KEY (Email, Passport_Number),
    FOREIGN KEY (Email) REFERENCES Customer(Email)
);

CREATE TABLE Payment_Info (
    Card_Type VARCHAR(20),
    Card_Number VARCHAR(20) PRIMARY KEY,
    Name_on_Card VARCHAR(100),
    Expiration_Date DATE
);

CREATE TABLE Seat_Availability (
    Flight_Num INT,
    Seat_Number VARCHAR(10),
    Is_Available BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (Flight_Num, Seat_Number),
    FOREIGN KEY (Flight_Num) REFERENCES Flight(Flight_Num)
);

CREATE TABLE Ticket (
    Ticket_ID INT PRIMARY KEY,
    Flight_Num INT,
    Seat_Number VARCHAR(10),
    Date_of_Birth DATE,
    Age INT,
    -- Age INT AS (YEAR(CURRENT_DATE) - YEAR(Date_of_Birth)),
    Sold_Price DECIMAL(10, 2),  
    Email VARCHAR(254),  -- Adding a reference to identify the customer

    FOREIGN KEY (Flight_Num, Seat_Number) REFERENCES Seat_Availability(Flight_Num, Seat_Number),
    FOREIGN KEY (Flight_Num) REFERENCES Flight(Flight_Num),
    FOREIGN KEY (Email) REFERENCES Customer(Email)
);




CREATE TABLE Booked (
    Email VARCHAR(100),
    Ticket_ID INT,
    Payment_Card_Number VARCHAR(20),
    PRIMARY KEY (Email, Ticket_ID),
    FOREIGN KEY (Email) REFERENCES Customer(Email),
    FOREIGN KEY (Ticket_ID) REFERENCES Ticket(Ticket_ID),
    FOREIGN KEY (Payment_Card_Number) REFERENCES Payment_Info(Card_Number)
);

CREATE TABLE Airline_Staff (
    Username VARCHAR(50) PRIMARY KEY,
    Passcode VARCHAR(50),
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Date_of_Birth DATE
);

CREATE TABLE Airline_Staff_Email (
    Username VARCHAR(50),
    Email VARCHAR(100),
    PRIMARY KEY (Username, Email),
    FOREIGN KEY (Username) REFERENCES Airline_Staff(Username)
);

CREATE TABLE Airline_Staff_Phone (
    Username VARCHAR(50),
    Phone VARCHAR(15),
    PRIMARY KEY (Username, Phone),
    FOREIGN KEY (Username) REFERENCES Airline_Staff(Username)
);

CREATE TABLE Works_For (
    Username VARCHAR(50),
    Airline_Name VARCHAR(100),
    PRIMARY KEY (Username, Airline_Name),
    FOREIGN KEY (Username) REFERENCES Airline_Staff(Username),
    FOREIGN KEY (Airline_Name) REFERENCES Airline(Airline_Name)
);

CREATE TABLE Rate_Comment (
    Email VARCHAR(100),
    Flight_Num INT,
    Comment TEXT,
    Rating INT CHECK (Rating BETWEEN 1 AND 5),
    PRIMARY KEY (Email, Flight_Num),
    FOREIGN KEY (Email) REFERENCES Customer(Email),
    FOREIGN KEY (Flight_Num) REFERENCES Flight(Flight_Num)
);

CREATE TABLE Purchase (
    Email VARCHAR(100),
    Ticket_ID INT,
    Purchase_Time TIME,
    Purchase_Date DATE,
    First_Name VARCHAR(50),
    Last_Name VARCHAR(50),
    Date_of_Birth DATE,
    PRIMARY KEY (Email, Ticket_ID),
    FOREIGN KEY (Email) REFERENCES Customer(Email),
    FOREIGN KEY (Ticket_ID) REFERENCES Ticket(Ticket_ID))

