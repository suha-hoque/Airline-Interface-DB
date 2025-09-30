

from flask import Flask, render_template, request, session, url_for, redirect, jsonify
import pymysql.cursors
import hashlib  # for MD5 hashing suggested in part 3
from datetime import datetime, timedelta
import io
from decimal import Decimal 
import base64


app = Flask(__name__)
conn = pymysql.connect(host='localhost',
                      user='root',
                      password='',
                      db='Final-Demo', #make sure to edit this to whatever you named the db
                      charset='utf8mb4',
                      cursorclass=pymysql.cursors.DictCursor)

#The purpose of this file is to initialze the application, define flask routes for each use case, and allow a connection to the database. It is where all of our queries are located. 
@app.route('/')
def hello():
    return render_template('index.html')

# below we use roles because we want to differentiate between when the customer is using the app and when the airline staff uses the app
@app.route('/login')
def login(): #login for both airline staff and customers work in a similar way. Essentially we are accessing all the attributes associated to either airline staff or customer while ensuring that the login details (username and password) matches whats saved in the DB, of course with the MD5 hashing implemented as well.

    role = request.args.get('role')
    if role == 'customer':  # if the role is equal to customer then we will render the customer_login.html page
        return render_template('customer_login.html')  # rendering this file from the templates page
    elif role == 'staff':  # if the role is equal to staff then we will render the staff_login.html page
        return render_template('staff_login.html')  # rendering this file from the templates page
    else:  # if there is no role, go to the homepage
        return redirect(url_for('hello'))

@app.route('/register') #registration for both cases generally work with 2 queries. First one just ensures that whatever primary key email/username is unique, and not used before by another user. After this check, the second query goes through and its just a simple insertion of the necessary attributes of either the customer or the staff.
def register():
    role = request.args.get('role')
    if role == 'customer':  # if the role is equal to customer then we will render the customer_register.html page
        return render_template('customer_register.html')  # rendering this file from the templates page
    elif role == 'staff':  # if the role is equal to staff then we will render the staff_register.html page
        #Additionally with airline staff since the staff can only work with an existing airline we check for that before allowing the registration. Therefore when testing the program make sure to access the phpmyadmin in order to insert at least one airline otherwise registration won't work.
        return render_template('staff_register.html')  # rendering this file from the templates page
    else:
        return redirect(url_for('hello'))  # if there is no role, go to the homepage



#
@app.route('/customer_loginAuth', methods=['POST']) 
def customer_loginAuth():
    email = request.form['email']
    password = request.form['password']
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM Customer WHERE Email = %s and Passcode = %s'
    cursor.execute(query, (email, hashed_password))
    data = cursor.fetchone()
    cursor.close()
    
    if data:
        session['email'] = email
        session['role'] = 'customer'
        session['first_name'] = data['First_Name']  # Store first name in the session
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or password'
        return render_template('customer_login.html', error=error)


@app.route('/select_seat/<flight_num>')
def select_seat(flight_num):
    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        
        # Get seats and their availability
        cursor.execute("""
            SELECT Seat_Number, Is_Available
            FROM Seat_Availability
            WHERE Flight_Num = %s
        """, (flight_num,))
        
        seats = cursor.fetchall()
        
        if not seats:
            return jsonify({'error': 'No seats found for this flight'})
            
        return jsonify({'seats': seats})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': 'An error occurred while loading seats'})
        
    finally:
        if cursor:
            cursor.close()


@app.route('/customer_registerAuth', methods=['POST'])
def customer_registerAuth():
    email = request.form['email']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    building_num = request.form['building_num']
    street_name = request.form['street_name']
    apartment_num = request.form.get('apartment_num', None)
    city = request.form['city']
    state = request.form['state']
    zip_code = request.form['zip_code']
    date_of_birth = request.form['date_of_birth']

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    cursor = conn.cursor()

    # Check if the email already exists
    query = 'SELECT * FROM Customer WHERE Email = %s'
    cursor.execute(query, (email,))
    data = cursor.fetchone()

    if data:
        cursor.close()
        error = "This email is already registered."
        return render_template('customer_register.html', error=error)

    insert_query = '''
        INSERT INTO Customer (Email, First_Name, Last_Name, Passcode, Building_Num, 
                              Street_Name, Apartment_Num, City, State, Zip_Code, Date_of_Birth)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    '''
    cursor.execute(insert_query, (
        email, first_name, last_name, hashed_password, building_num, 
        street_name, apartment_num, city, state, zip_code, date_of_birth
    ))
    conn.commit()
    cursor.close()

    return redirect(url_for('login', role='customer'))


@app.route('/staff_registerAuth', methods=['POST'])
def staff_registerAuth():
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    password = request.form['password']
    date_of_birth = request.form['date_of_birth']
    email = request.form['email']
    phone = request.form['phone']
    airline = request.form['airline']

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    cursor = conn.cursor()

    # check if username is already taken
    query = 'SELECT * FROM Airline_Staff WHERE Username = %s'
    cursor.execute(query, (username,))
    data = cursor.fetchone()

    if data:
        cursor.close()
        error = "This username is taken."
        return render_template('staff_register.html', error=error)
    
    # check to see if airline exists
    query_airline = 'SELECT * FROM Airline WHERE Airline_Name = %s'
    cursor.execute(query_airline, (airline,))
    airline_data = cursor.fetchone()

    if not airline_data:
        cursor.close()
        error = f"Airline does not exist."
        return render_template('staff_register.html', error=error)

    try:
        insert_query = """
            INSERT INTO Airline_Staff (Username, First_Name, Last_Name, Passcode, Date_of_Birth)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (username, first_name, last_name, hashed_password, date_of_birth))
        
        # insert into email
        query_email = """
            INSERT INTO Airline_Staff_Email (Username, Email)
            VALUES (%s, %s)
        """
        cursor.execute(query_email, (username, email))
        
        #insert into phone
        query_phone = """
            INSERT INTO Airline_Staff_Phone (Username, Phone)
            VALUES (%s, %s)
        """    
        cursor.execute(query_phone, (username, phone))
        
        # add airline the staff works at
        query_works_for = """
            INSERT INTO Works_For (Username, Airline_Name)
            VALUES (%s, %s)
        """
        cursor.execute(query_works_for, (username, airline))

        conn.commit()

    except Exception as e:
        conn.rollback()
        cursor.close()
        return f"Error during registration: {str(e)}"
    
    cursor.close()
    return redirect(url_for('login', role='staff'))



@app.route('/staff_loginAuth', methods=['POST'])
def staff_loginAuth():
    username = request.form['username']
    password = request.form['password']
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    cursor = conn.cursor()
    query = 'SELECT * FROM Airline_Staff WHERE Username = %s and Passcode = %s'
    cursor.execute(query, (username, hashed_password))
    data = cursor.fetchone()
    cursor.close()
    
    if data:
        session['username'] = username
        session['role'] = 'staff'
        session['first_name'] = data['First_Name']  # Store first name in the session
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or password'
        return render_template('staff_login.html', error=error)





@app.route('/home')
def home():
    # Redirect to specific home page based on role
    if 'role' in session:
        cursor = conn.cursor()
        if session['role'] == 'customer':  # Check if the user is a customer based on session role
            email = session['email']
            # Query to fetch the first name of the customer
            query = 'SELECT First_Name FROM Customer WHERE Email = %s'
            cursor.execute(query, (email,))
            data = cursor.fetchone()
            cursor.close()
            first_name = data['First_Name'] if data else 'Customer'
            return render_template('customer_home.html', first_name=first_name)
        elif session['role'] == 'staff':  # Check if the user is a staff member based on session role
            username = session['username']
            # Query to fetch the first name of the staff member
            query = 'SELECT First_Name FROM Airline_Staff WHERE Username = %s'
            cursor.execute(query, (username,))
            data = cursor.fetchone()
            query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
            cursor.execute(query_airline, (username,))
            staff_airline = cursor.fetchone()
            airline_name = staff_airline['Airline_Name']
            first_name = data['First_Name'] if data else 'Staff'
            cursor.close()
            return render_template('staff_home.html', first_name=first_name, airline_name=airline_name)
    else:
        return redirect(url_for('hello'))  # If no valid session role, redirect to homepage



@app.route('/search_flights', methods=['POST'])
#A form to search for flights based on either the departure or arrival airports and one-way or round-trip, and specified dates.
#Display of matching flight results or a message if no matches are found.

def search_flights():
   # Retrieve form data
   departure_code = request.form['departure_code']
   arrival_code = request.form['arrival_code']
   trip_type = request.form['trip_type']
   departure_date = request.form['departure_date']
   return_date = request.form.get('return_date') if trip_type == 'round-trip' else None
   target_page = request.form.get('target_page', 'index')  # Default to 'index'


   cursor = conn.cursor()


   # when user is not logged in they can retrieve all the attributes stored in flight given that it fetches the row that matches the departure, arrival code, and the specific departure date, and accordingly the same logic for round trips.

   query = '''
       SELECT * FROM Flight
       WHERE Departure_Code = %s AND Arrival_Code = %s AND Departure_Date = %s
   '''
   params = [departure_code, arrival_code, departure_date]


   # If round-trip, add query for return flight
   if trip_type == 'round-trip' and return_date:
       query += ' UNION ALL SELECT * FROM Flight WHERE Departure_Code = %s AND Arrival_Code = %s AND Departure_Date = %s'
       params.extend([arrival_code, departure_code, return_date])


   cursor.execute(query, params)
   flights = cursor.fetchall()
   cursor.close()


   # Add a flag for past flights and filter them out
   current_date = datetime.now().date()
   valid_flights = []
   has_past_flights = False


   for flight in flights:
       flight_data = dict(flight)  # Convert to a dictionary for easier manipulation
       flight_date = flight_data['Departure_Date']  # Assuming this is already a datetime.date
       if flight_date < current_date:
           has_past_flights = True
       else:
           valid_flights.append(flight_data)


   # Render the appropriate template based on the target_page
   if target_page == 'index':
       return render_template('index.html', flights=valid_flights, has_past_flights=has_past_flights)
   elif target_page == 'customer_home':
       return render_template('customer_home.html', flights=valid_flights, has_past_flights=has_past_flights)
   else:
       return "Page not found", 404


@app.route('/flight_status', methods=['POST']) #user when not logged in can get the flight status of certain flights when inputting the flight number, airline name, and departure/arrival date. The query works by selecting all the attributes from flight with the condition that the user’s imputed flight number, airline name, and departure/arrival date matches with a row in the DB’s flight table.

def flight_status():
    airline_name = request.form['airline_name']
    flight_num = request.form['flight_num']
    date = request.form['date']
    date_type = request.form['date_type']  # 'departure' or 'arrival'

    cursor = conn.cursor()
    query = f'''
        SELECT 
            Flight_Num, 
            Flight_Status, 
            Airline_Name,
            {date_type}_Date AS Date, 
            {date_type}_Time AS Time, 
            Departure_Code, 
            Arrival_Code, 
            %s AS Date_Type
        FROM Flight
        WHERE Airline_Name = %s AND Flight_Num = %s AND {date_type}_Date = %s
    '''
    cursor.execute(query, (date_type, airline_name, flight_num, date))
    flight_status_results = cursor.fetchall()
    cursor.close()

    # Render the template with the flight status results
    return render_template('index.html', flight_status_results=flight_status_results)


@app.route('/rate_flight', methods=['GET', 'POST'])
def rate_flight():
  #the way rate flight’s query works is by accessing all the flights a user took by matching the ticket’s flight num and the flight table’s flight num, then selects only the flights that are already landed, and not rated by this user yet.


    if 'email' not in session:
        return redirect('/login')
    

    if request.method == 'GET':
        try:
           
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
           
            cursor.execute("""
                SELECT DISTINCT f.Flight_Num, 
                       f.Departure_Code, 
                       f.Arrival_Code, 
                       f.Departure_Date, 
                       f.Airline_Name,
                       f.Departure_Time
                FROM Flight f
                JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                JOIN (
                    SELECT Ticket_ID, Email FROM Purchase
                    UNION
                    SELECT Ticket_ID, Email FROM Booked
                ) b ON t.Ticket_ID = b.Ticket_ID
                LEFT JOIN Rate_Comment rc ON f.Flight_Num = rc.Flight_Num AND b.Email = rc.Email
                WHERE b.Email = %s 
                AND CONCAT(f.Arrival_Date, ' ', f.Arrival_Time) < NOW()
                AND rc.Flight_Num IS NULL
            """, (session['email'],))
            
            flights_to_rate = cursor.fetchall()
            
            return render_template('rate_flight.html', flights=flights_to_rate)
        
        except pymysql.Error as err:
            print(f"Database error: {err}")
            return "Error fetching flights", 500
        
        finally:
            if 'cursor' in locals():
                cursor.close()
    
   
    elif request.method == 'POST':
        try:
            
            flight_num = request.form['flight_num']
            rating = request.form['rating']
            comment = request.form.get('comment', '')  
            
           
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            
            
            cursor.execute("""
                SELECT 1 
                FROM Flight f
                JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                JOIN (
                    SELECT Ticket_ID, Email FROM Purchase
                    UNION
                    SELECT Ticket_ID, Email FROM Booked
                ) b ON t.Ticket_ID = b.Ticket_ID
                WHERE b.Email = %s 
                  AND f.Flight_Num = %s
                  AND CONCAT(f.Arrival_Date, ' ', f.Arrival_Time) < NOW()
            """, (session['email'], flight_num))
            
            flight_exists = cursor.fetchone()
            
            
            cursor.execute("""
                SELECT 1 
                FROM Rate_Comment 
                WHERE Email = %s AND Flight_Num = %s
            """, (session['email'], flight_num))
            
            already_rated = cursor.fetchone()
            
            
            if not flight_exists:
                return "Invalid flight or you did not take this flight", 400
            
            if already_rated:
                return "You have already rated this flight", 400
            
            if not (1 <= int(rating) <= 5):
                return "Rating must be between 1 and 5", 400
            
           
            cursor.execute("""
                INSERT INTO Rate_Comment (Email, Flight_Num, Comment, Rating)
                VALUES (%s, %s, %s, %s)
            """, (session['email'], flight_num, comment, rating))
            
            
            conn.commit()
            
            
            return redirect('/customer_home')
        
        except pymysql.Error as err:
            
            conn.rollback()
            print(f"Database error: {err}")
            return "Error submitting rating", 500
        
        except Exception as e:
            
            conn.rollback()
            print(f"Unexpected error: {e}")
            return "An unexpected error occurred", 500
        
        finally:
            if 'cursor' in locals():
                cursor.close()



@app.route('/customer_home')
def customer_home():
   
    if 'email' not in session:
        return redirect('/login')
    
    return render_template('customer_home.html', email=session['email'])

@app.route('/cancel_ticket', methods=['POST'])
def cancel_ticket():
   #when we want to cancel the ticket, we want to ensure that the user can only cancel a ticket they had purchased.

    cursor = None

    try:
        # Check if user is logged in
        if 'email' not in session:
            return "Please log in first", 401

        email = session['email']
        ticket_id = request.form['ticket_id']

        # Create database cursor
        cursor = conn.cursor(pymysql.cursors.DictCursor)

        # first we check if this is the user's valid tiket
        cursor.execute("""
            SELECT t.Flight_Num, t.Seat_Number, f.Departure_Date, f.Departure_Time
            FROM Ticket t
            JOIN Flight f ON t.Flight_Num = f.Flight_Num
            JOIN Booked b ON t.Ticket_ID = b.Ticket_ID
            WHERE t.Ticket_ID = %s AND b.Email = %s
        """, (ticket_id, email))
        ticket_info = cursor.fetchone()

        #ticket exists? check 
        if not ticket_info:
            return "Ticket not found or does not belong to you", 400
        
        departure_time = (datetime.min + ticket_info['Departure_Time']).time()
        flight_datetime = datetime.combine(ticket_info['Departure_Date'], departure_time)
        current_datetime = datetime.now()
        
        if flight_datetime - current_datetime <= timedelta(hours=24):
            return "Ticket cannot be canceled less than 24 hours before flight", 400


        conn.begin()

        # delete the b ooking record
        cursor.execute("DELETE FROM Booked WHERE Ticket_ID = %s", (ticket_id,))

        # delete the dpurchsed record
        cursor.execute("DELETE FROM Purchase WHERE Ticket_ID = %s", (ticket_id,))

        # delete the ticket
        cursor.execute("DELETE FROM Ticket WHERE Ticket_ID = %s", (ticket_id,))

        #seat is available again
        cursor.execute("""
            UPDATE Seat_Availability 
            SET Is_Available = TRUE 
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (ticket_info['Flight_Num'], ticket_info['Seat_Number']))

    
        conn.commit()

      

        return redirect('/customer_home')

    except KeyError as e:
        return f"Missing information: {str(e)}", 400

    except pymysql.Error as err: #some error handling
        if conn:
            conn.rollback()
        print(f"Database error: {err}")
        return "Error processing ticket cancellation", 500

    except Exception as e:
       
        if conn:
            conn.rollback()
        print(f"Unexpected error: {e}")
        return "An unexpected error occurred", 500

    finally:
       
        if cursor:
            cursor.close()



@app.route('/view_flights', methods=['GET']) #the main difference in the queries between the past and future viewing of flights is the comparison sign between the curr-date and the departure date in our DB. Otherwise the query is almost exactly the same. It works by accessing the flight table and the ticket table and ensuring that this flight is purchased by the person logged in. We do this by the join statements for instance  JOIN Ticket t ON f.Flight_Num = t.Flight_Num, and so on.



def view_flights():
    if 'email' not in session:
        return redirect(url_for('login'))

    email = session['email']
    first_name = session.get('first_name', 'Guest')
    query_type = request.args.get('type', 'future')

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            if query_type == 'past':
                query = """
                    SELECT f.Flight_Num, f.Departure_Date, f.Departure_Time, f.Arrival_Date, f.Arrival_Time,
                           f.Departure_Code, f.Arrival_Code, f.Airline_Name, f.Base_Ticket_Price, 
                           f.Flight_Status, t.Sold_Price, t.Ticket_ID
                    FROM Flight f
                    JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                    JOIN Purchase p ON t.Ticket_ID = p.Ticket_ID
                    JOIN Airport dep ON f.Departure_Code = dep.Airport_Code
                    JOIN Airport arr ON f.Arrival_Code = arr.Airport_Code
                    WHERE p.Email = %s 
                    AND CONCAT(f.Arrival_Date, ' ', f.Arrival_Time) < NOW()
                    ORDER BY f.Arrival_Date DESC, f.Arrival_Time DESC
                """
            else:
                query = """
                    SELECT f.Flight_Num, f.Departure_Date, f.Departure_Time, f.Arrival_Date, f.Arrival_Time,
                           f.Departure_Code, f.Arrival_Code, f.Airline_Name, f.Base_Ticket_Price, 
                           f.Flight_Status, t.Sold_Price, t.Ticket_ID
                    FROM Flight f
                    JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                    JOIN Purchase p ON t.Ticket_ID = p.Ticket_ID
                    JOIN Airport dep ON f.Departure_Code = dep.Airport_Code
                    JOIN Airport arr ON f.Arrival_Code = arr.Airport_Code
                    WHERE p.Email = %s 
                    AND CONCAT(f.Arrival_Date, ' ', f.Arrival_Time) >= NOW()
                    ORDER BY f.Departure_Date ASC, f.Departure_Time ASC
                """
            cursor.execute(query, (email,))
            flights = cursor.fetchall()

            cursor.execute("""
                SELECT DISTINCT f.Flight_Num,
                       f.Departure_Code,
                       f.Arrival_Code,
                       f.Departure_Date,
                       f.Airline_Name,
                       f.Departure_Time,
                       t.Ticket_ID
                FROM Flight f
                JOIN Ticket t ON f.Flight_Num = t.Flight_Num
                JOIN Purchase p ON t.Ticket_ID = p.Ticket_ID
                LEFT JOIN Rate_Comment rc ON f.Flight_Num = rc.Flight_Num AND p.Email = rc.Email
                WHERE p.Email = %s
                AND CONCAT(f.Arrival_Date, ' ', f.Arrival_Time) < NOW()
                AND rc.Flight_Num IS NULL
            """, (email,))
            flights_to_rate = cursor.fetchall()

        return render_template(
            'customer_home.html',
            flights=flights,
            flights_to_rate=flights_to_rate,
            query_type=query_type,
            first_name=first_name
        )
    except Exception as e:
        print(f"Error fetching flights: {e}")
        return redirect(url_for('customer_home'))
    
@app.route('/track_spending', methods=['GET', 'POST'])
def track_spending():
    cursor = None
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        email = session.get('email')

        if not email:
            return "User not logged in.", 401

        # Calculate total spent in the last year
        cursor.execute("""
            SELECT SUM(T.Sold_Price) AS Total_Spent
            FROM Purchase P
            JOIN Ticket T ON P.Ticket_ID = T.Ticket_ID
            WHERE P.Email = %s AND P.Purchase_Date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 YEAR)
        """, (email,))
        total_spent_last_year = cursor.fetchone()['Total_Spent'] or Decimal('0.00')

        # Calculate spending in the last 6 months grouped by month
        cursor.execute("""
            SELECT DATE_FORMAT(P.Purchase_Date, '%%Y-%%m') AS Month, 
                SUM(T.Sold_Price) AS Total_Spent
            FROM Purchase P
            JOIN Ticket T ON P.Ticket_ID = T.Ticket_ID
            WHERE P.Email = %s 
                AND P.Purchase_Date BETWEEN DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH) AND CURRENT_DATE
            GROUP BY Month
            ORDER BY Month DESC
        """, (email,))
        last_6_months_spending = cursor.fetchall()

        # Default range spending variables for GET requests
        total_spent_range = None
        range_month_wise_spending = None
        start_date = None
        end_date = None

        # Handle POST requests for custom date range
        if request.method == 'POST':
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')

            if start_date and end_date:
                cursor.execute("""
                    SELECT SUM(T.Sold_Price) AS Total_Spent
                    FROM Purchase P
                    JOIN Ticket T ON P.Ticket_ID = T.Ticket_ID
                    WHERE P.Email = %s AND P.Purchase_Date BETWEEN %s AND %s
                """, (email, start_date, end_date))
                total_spent_range = cursor.fetchone()['Total_Spent'] or Decimal('0.00')

                cursor.execute("""
                    SELECT DATE_FORMAT(P.Purchase_Date, '%%Y-%%m') AS Month, 
                           SUM(T.Sold_Price) AS Total_Spent
                    FROM Purchase P
                    JOIN Ticket T ON P.Ticket_ID = T.Ticket_ID
                    WHERE P.Email = %s 
                      AND P.Purchase_Date BETWEEN %s AND %s
                    GROUP BY Month
                    ORDER BY Month DESC
                """, (email, start_date, end_date))
                range_month_wise_spending = cursor.fetchall()

        # Render the page with the default or custom data
        return render_template(
            'customer_home.html',
            total_spent_last_year=total_spent_last_year,
            last_6_months_spending=last_6_months_spending,
            total_spent_range=total_spent_range,
            range_month_wise_spending=range_month_wise_spending,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500
    finally:
        if cursor:
            cursor.close()


@app.route('/purchase_ticket', methods=['POST'])
def purchase_ticket():
    #first we simply display all the seats and their availability status given a flight number, from the seat availability table.
    cursor = None
    ticket_id = None

    try:
        # get form data
        flight_num = request.form['flight_num']
        seat_number = request.form['seat_number']
        card_type = request.form['card_type']
        card_number = request.form['card_number']
        name_on_card = request.form['name_on_card']
        expiration_date = request.form['expiration_date']
        email = session['email']

      
        try:
            month, year = expiration_date.split('/')
            expiration_date = f"20{year}-{month}-01"
        except ValueError:
            return "Invalid expiration date format. Please use MM/YY", 400

        cursor = conn.cursor(pymysql.cursors.DictCursor)

       
        cursor.execute("""
            SELECT * FROM Flight
            WHERE Flight_Num = %s 
        """, (flight_num,))
        flight = cursor.fetchone()

        if not flight:
            return "Sorry, tickets for this flight are not available", 400

      
        cursor.execute("""
            SELECT Date_of_Birth, First_Name, Last_Name
            FROM Customer
            WHERE Email = %s
        """, (email,))
        customer = cursor.fetchone()

        
        cursor.execute("""
            SELECT Is_Available FROM Seat_Availability
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (flight_num, seat_number))
        seat = cursor.fetchone()

        if not seat or not seat['Is_Available']:
            return "Sorry, this seat is not available", 400

        
        cursor.execute("""
            SELECT 
                COUNT(*) AS total_seats,
                SUM(CASE WHEN Is_Available = TRUE THEN 1 ELSE 0 END) AS available_seats,
                COUNT(*) - SUM(CASE WHEN Is_Available = TRUE THEN 1 ELSE 0 END) AS taken_seats
            FROM Seat_Availability
            WHERE Flight_Num = %s
        """, (flight_num,))
        seat_stats = cursor.fetchone()

        total_seats = seat_stats['total_seats']
        available_seats = seat_stats['available_seats']
        base_price = flight['Base_Ticket_Price']

        # sold price
        if available_seats <= (total_seats * 0.3):  # 80% or more seats taken
            sold_price = float(base_price) * 1.25  # Increase by 25%
        else:
            sold_price = float(base_price)


        conn.begin()

        #From this we can select a seat , and flight num and seat num is autofilled and then user must put in all the payment details such as card type, number, expiration date, name on card and cvv. 
        cursor.execute("""
            INSERT INTO Payment_Info 
            (Card_Type, Card_Number, Name_on_Card, Expiration_Date)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            Card_Type = VALUES(Card_Type),
            Name_on_Card = VALUES(Name_on_Card),
            Expiration_Date = VALUES(Expiration_Date)
        """, (card_type, card_number, name_on_card, expiration_date))
#After some basic validation of inputs, this is the main query that inserts into payment info all the info that is secure to store, so basically all the attributes except the cvv. 

        # generating the ticket ID
        cursor.execute("SELECT MAX(Ticket_ID) AS max_id FROM Ticket")
        last_ticket_id = cursor.fetchone()['max_id']
        ticket_id = last_ticket_id + 1 if last_ticket_id else 1

        # Create ticket record with calculated sold price
        cursor.execute("""
            INSERT INTO Ticket
            (Ticket_ID, Flight_Num, Seat_Number, Date_of_Birth, Email, Sold_Price)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (ticket_id, flight_num, seat_number, customer['Date_of_Birth'], email, sold_price))

        # Update seat availability
        cursor.execute("""
            UPDATE Seat_Availability
            SET Is_Available = FALSE
            WHERE Flight_Num = %s AND Seat_Number = %s
        """, (flight_num, seat_number))

        # Record purchase details
        cursor.execute("""
            INSERT INTO Purchase
            (Email, Ticket_ID, Purchase_Date, Purchase_Time,
             First_Name, Last_Name, Date_of_Birth)
            VALUES (%s, %s, CURRENT_DATE, CURRENT_TIME, %s, %s, %s)
        """, (email, ticket_id,
              customer['First_Name'],
              customer['Last_Name'],
              customer['Date_of_Birth']))

        # Record booking information
        cursor.execute("""
            INSERT INTO Booked
            (Email, Ticket_ID, Payment_Card_Number)
            VALUES (%s, %s, %s)
        """, (email, ticket_id, card_number))

        conn.commit()
        return redirect('/customer_home')
#Above are the 4 main inserts we need to execute when purchasing. First being generating a ticket and associating it to the specific customer.  Next we set the seat availability with that flight number and seat as not available or false. Nest inserts, we will insert the purchase details into the purchase table while also storing the purchase date and time using curr date and time. Lastly we insert the ticket-id and other relevant attributes such as the email and payment card number to the booked table, this way we have a link between the email and the ticket-id.

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error: {e}")
        return str(e), 500
    finally:
        if cursor:
            cursor.close()






















# use case 1 where staff can view flights. the default view are flights for the next 30 days
@app.route('/view_staff_flights', methods=['GET', 'POST'])
def view_staff_flights():
    # check to see if the role of user is staff
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']
    flights = []
    customers = []

    # the default is to show the future flights for the next 30 days
    if request.method == 'GET':
        query_for_flights = """
                    SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
                    FROM Flight
                    WHERE Airline_Name = %s 
                    AND (
                        (Departure_Date BETWEEN CURDATE() AND (CURDATE() + INTERVAL 30 DAY)) OR
                        (Departure_Date = CURDATE() AND Departure_Time > CURTIME())
                    )
        """
        cursor.execute(query_for_flights, (airline_name,))
        flights = cursor.fetchall()

    # filters that include date range or staff can choose a source or destination airport or both for search
    elif request.method == 'POST':
        source = request.form.get('source')
        destination = request.form.get('destination')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        # fetch all the flights associated with the airline the staff works at
        query_for_flights = """
            SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
            FROM Flight
            WHERE Airline_Name = %s
        """
        params = [airline_name]  # used to extend query_for_flights based on form info

        if start_date and end_date: # require both start and end date for the date range
            query_for_flights += " AND Departure_Date BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        if start_date and not end_date:
            return "please specify end date"
        if not start_date and end_date:
            return "please specify start date"   
        
        if source:  # add onto the where clause
            query_for_flights += " AND Departure_Code = %s"
            params.append(source)
        if destination:  # add onto the where clause
            query_for_flights += " AND Arrival_Code = %s"
            params.append(destination)

        cursor.execute(query_for_flights, params)
        flights = cursor.fetchall()

    # show all customers and their flights based on the ticket purchased
    # collecting data to send to the view_staff_flights page
    query_customers = """
    SELECT DISTINCT Customer.Email, Customer.First_Name, Customer.Last_Name,
           Flight.Flight_Num, Flight.Departure_Date, Flight.Departure_Time
    FROM Ticket
    JOIN Customer ON Ticket.Email = Customer.Email
    JOIN Flight ON Ticket.Flight_Num = Flight.Flight_Num
    WHERE Flight.Airline_Name = %s
    ORDER BY Flight.Departure_Date, Flight.Departure_Time;
    """
    cursor.execute(query_customers, (airline_name,))
    customers = cursor.fetchall()

    cursor.close()
    return render_template('view_staff_flights.html', flights=flights, customers=customers)


# use case 3 where a staff can change the flight status of future flights
@app.route('/change_flight_status', methods=['GET', 'POST']) 
def change_flight_status():
    # make sure only airline staff can do this action
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))

    username = session['username'] 
    cursor = conn.cursor()
    query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Airline for Airline Staff Not Found"
    airline_name = staff_airline['Airline_Name']

    if request.method == 'POST':
        # get the needed info from forms
        flight_num = request.form.get('flight_num')
        new_status = request.form.get('status')

        # make sure flight num and new staus is included 
        if not flight_num or not new_status:
            return "Flight number or status not provided"
       
        try:
            # use the form info to update the flight status to the new status
            update_query = """
                UPDATE Flight
                SET Flight_Status = %s
                WHERE Flight_Num = %s AND Airline_Name = %s
            """
            cursor.execute(update_query, (new_status, flight_num, airline_name))
            conn.commit()
        
        except Exception as e:    
            conn.rollback()
            cursor.close()
            return f"Unable to update flight status. {str(e)}"
        
        cursor.close()
        return redirect(url_for('change_flight_status'))

    # only update the flight status of future flights (check to see if departure date is past the current date)
    query_for_flights = """
        SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
        FROM Flight
        WHERE Airline_Name = %s AND Departure_Date >= CURDATE()
    """

    cursor.execute(query_for_flights, (airline_name,))
    flights = cursor.fetchall()
    cursor.close()
    return render_template('change_flight_status.html', flights=flights, airline_name=airline_name)


# use case 4 of adding a new airplane for the airline
@app.route('/add_airplane', methods=['GET', 'POST'])
def add_airplane():
    # check to ensure it's an airline staff
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        query = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            airplane_id = request.form.get('airplane_id')
            num_seats = request.form.get('num_seats')
            manufacturer = request.form.get('manufacturer')
            model_num = request.form.get('model_num')
            manufacture_date = request.form.get('manufacture_date')

            # make sure all fields are filled by the user
            if not (airplane_id and num_seats and manufacturer and model_num and manufacture_date):
                return "Fill out all fields."

            try:
                conn.begin()
                # get the current date to see if the given manufacturing date is greater than the current date 
                # the manufacturing date cannot be in the future
                query_date = "SELECT CURDATE()"
                cursor.execute(query_date)
                current_date = cursor.fetchone()['CURDATE()']
                
                if manufacture_date > str(current_date):
                    return "The manufacturing date cannot exceed the current date."

                # make sure this airplane does not already exist in the airline
                query_multiple = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_multiple, (airplane_id, airline_name))
                existing_airplane = cursor.fetchone()
                
                # this airplane with airplane id already exists in the airline (not allowed)
                if existing_airplane:
                    return f"Airplane with ID {airplane_id} already exists."

                # create new airplane by inserting into Airplane
                query_insert_airplane = """
                    INSERT INTO Airplane (Airline_Name, Airplane_ID, Number_of_Seats, 
                                          Manufacturing_Company, Model_Num, Manufacturing_Date, Age) 
                    VALUES (%s, %s, %s, %s, %s, %s, YEAR(CURDATE()) - YEAR(%s))
                """
                cursor.execute(query_insert_airplane, (airline_name, airplane_id, num_seats, manufacturer, 
                                              model_num, manufacture_date, manufacture_date))
                
                # update the owns table to show which airline owns this airplane
                query_insert_owns = """
                    INSERT INTO Owns (Airline_Name, Airplane_ID) 
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert_owns, (airline_name, airplane_id))
                conn.commit()

                # get all the airplanes to show for confirmation
                query_airplanes = """
                    SELECT Airline_Name, Airplane_ID, Number_of_Seats, 
                           Manufacturing_Company, Model_Num, Manufacturing_Date, Age
                    FROM Airplane
                    WHERE Airline_Name = %s
                """
                cursor.execute(query_airplanes, (airline_name,))
                airplanes = cursor.fetchall()

                return render_template('airplane_confirmation.html', airplanes=airplanes, airline_name=airline_name)
            
            except Exception as e:
                conn.rollback()
                return f"Unable to add new airplane. {str(e)}"
        return render_template('add_airplane.html', airline_name=airline_name)
    
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()

# use case 5 of adding a airport to the airline
# updates the operates table which shows in which airports the airline operates from
@app.route('/add_airport', methods=['GET', 'POST'])
def add_airport():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        # get the airline the staff works for
        query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            airport_code = request.form.get('airport_code')
            airport_name = request.form.get('airport_name')
            city = request.form.get('city')
            country = request.form.get('country')
            num_terminals = request.form.get('num_terminals')
            airport_type = request.form.get('airport_type')

            if not (airport_code and airport_name and city and country and num_terminals and airport_type):
                return "Fill out all fields."

            try:
                # check if the airline operates in this airport already
                query_operates = """
                    SELECT * 
                    FROM Operates 
                    WHERE Airline_Name = %s AND Airport_Code = %s
                """
                cursor.execute(query_operates, (airline_name, airport_code))
                existing = cursor.fetchone()

                if existing:
                    return "The airline already operates in this airport."
                
                # check if the airport (identified by airport_code) already exists
                query_airport = """
                    SELECT * 
                    FROM Airport 
                    WHERE Airport_Code = %s
                """
                cursor.execute(query_airport, (airport_code,))
                existing_airport = cursor.fetchone()

                # if the airport does not exist in the airport table, create new airport 
                if not existing_airport:
                    query_insert_airport = """
                        INSERT INTO Airport (Airport_Code, Airport_Name, City, Country, Number_of_Terminals, Airport_Type) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query_insert_airport, (airport_code, airport_name, city, country, num_terminals, airport_type))
                    conn.commit()

                # associate the airport with the airline through operates
                query_insert_operates = """
                    INSERT INTO Operates (Airline_Name, Airport_Code) 
                    VALUES (%s, %s)
                """
                cursor.execute(query_insert_operates, (airline_name, airport_code))
                conn.commit()

                # confirmation airport for staff
                query_airports = """
                    SELECT Airport_Code, Airport_Name, City, Country, Number_of_Terminals, Airport_Type
                    FROM Airport
                    WHERE Airport_Code = %s
                """
                cursor.execute(query_airports, (airport_code,))
                airport = cursor.fetchone()
                return render_template('airport_confirmation.html', airport=airport, airline_name=airline_name)

            except Exception as e:
                conn.rollback()
                return f"Unable to add airport. {str(e)}"
        return render_template('add_airport.html', airline_name=airline_name)
    
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()


# use case 9 which is to view earned revenue (done by checking purchase date)
@app.route('/view_earned_revenue', methods=['GET'])
def view_earned_revenue():
    #Handles date-range-based spending tracking and displays spending data for a user-specified date range

    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']

    # seeing if the purchase_date falls between current date and the date from a month ago
    # to sum up the sold_prices of tickets
    query_for_month = """
        SELECT SUM(Ticket.Sold_Price) AS Last_Month_Revenue
        FROM Purchase, Ticket, Flight
        WHERE Flight.Airline_Name = %s
            AND Purchase.Ticket_ID = Ticket.Ticket_ID
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND (
                Purchase.Purchase_Date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 MONTH) AND CURDATE()
                OR (Purchase.Purchase_Date = CURDATE() AND Purchase.Purchase_Time <= CURTIME())
            )
    """
    cursor.execute(query_for_month, (airline_name,))
    revenue_for_month = cursor.fetchone()['Last_Month_Revenue'] or 0
    
    # similar to query_for_month, check to see if the purchase date falls between current date and date one year ago
    query_for_year = """
        SELECT SUM(Ticket.Sold_Price) AS Last_Year_Revenue
        FROM Purchase, Ticket, Flight
        WHERE Flight.Airline_Name = %s
            AND Purchase.Ticket_ID = Ticket.Ticket_ID
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND (
                Purchase.Purchase_Date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE()
                OR (Purchase.Purchase_Date = CURDATE() AND Purchase.Purchase_Time <= CURTIME())
            )
    """
    cursor.execute(query_for_year, (airline_name,))
    revenue_for_year = cursor.fetchone()['Last_Year_Revenue'] or 0
    cursor.close()

    return render_template('view_earned_revenue.html', airline_name=airline_name, revenue_last_month=revenue_for_month,
                           revenue_last_year=revenue_for_year
    )

# use case 6 which allows staff to view average flight ratings and comments
@app.route('/view_flight_ratings', methods=['GET'])
def view_flight_ratings():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Airline for Airline Staff Not Found."
    
    airline_name = staff_airline['Airline_Name']

    # all the flights associated with the airline
    query_for_flights = """
        SELECT Flight_Num, Departure_Date, Departure_Code, Arrival_Date, Arrival_Code
        FROM Flight
        WHERE Airline_Name = %s
    """
    cursor.execute(query_for_flights, (airline_name,))
    flights = cursor.fetchall()

    # used to get each flight info with the customer rating and comment and used for display 
    flight_info = []
    for flight in flights:
        flight_num = flight['Flight_Num']
        departure_date = flight['Departure_Date']

        # joins rate_comment and flight to calculate average rating for the correct flight (flight_num)
        query_avg_rating = """
            SELECT AVG(Rating) AS Average_Rating
            FROM Rate_Comment, Flight
            WHERE Rate_Comment.Flight_Num = Flight.Flight_Num
                AND Rate_Comment.Flight_Num= %s 
                AND Flight.Departure_Date = %s
                AND Flight.Airline_Name = %s   
        """
        cursor.execute(query_avg_rating, (flight_num, departure_date, airline_name))
        rating = cursor.fetchone()['Average_Rating'] or 0

        # joins rate_comment and flight to get the correct comment, rating, and email for the flight
        query_comments = """
            SELECT Rate_Comment.Comment, Rate_Comment.Rating, Rate_Comment.Email
            FROM Rate_Comment, Flight
            WHERE Rate_Comment.Flight_Num = Flight.Flight_Num
                AND Rate_Comment.Flight_Num= %s 
                AND Flight.Departure_Date = %s
                AND Flight.Airline_Name = %s
        """
        cursor.execute(query_comments, (flight_num, departure_date, airline_name))
        comments = cursor.fetchall()

        # appending all the necessary info to show to staff 
        flight_info.append({
            'Flight_Num': flight_num,
            'Departure_Date': flight['Departure_Date'],
            'Arrival_Date': flight['Arrival_Date'],
            'Departure_Code': flight['Departure_Code'],
            'Arrival_Code': flight['Arrival_Code'],
            'Avg_Rating': rating,
            'Comments': comments
        })

    cursor.close()
    return render_template('view_flight_ratings.html', 
                           flights=flight_info, airline_name=airline_name)

# use case 8, view_frequent_customer which shows the most frequent customer from the past year
# also shows all flights customers have already taken 
@app.route('/view_frequent_customer', methods=['GET', 'POST'])
def view_frequent_customer():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
     
    username = session['username']
    cursor = conn.cursor()

    query = """
        SELECT Airline_Name 
        FROM Works_For 
        WHERE Username = %s
    """
    cursor.execute(query, (username,))
    staff_airline = cursor.fetchone()

    if not staff_airline:
        cursor.close()
        return "Airline for Airline Staff Not Found."
    airline_name = staff_airline['Airline_Name']
    
    # joining ticket, customer, and flight to make sure the correct customer (email) is chosen
    # grouping by customer email and then ordering by total flights which shows the number of flights 
    # a customer has taken. distinct is used in the count to make sure a customer is counted for a flight once
    # even if they purchased multiple tickets
    query_frequent = """
        SELECT Customer.Email, Customer.First_Name, Customer.Last_Name, 
        COUNT(DISTINCT Flight.Flight_Num) AS Total_Flights
        FROM Ticket, Customer, Flight
        WHERE Flight.Airline_Name = %s
            AND Ticket.Email = Customer.Email
            AND Ticket.Flight_Num = Flight.Flight_Num
            AND (
                (Flight.Departure_Date BETWEEN DATE_SUB(CURDATE(), INTERVAL 1 YEAR) AND CURDATE())
                OR (Flight.Departure_Date = CURDATE() AND Flight.Departure_Time < CURTIME())
            )    
        GROUP BY Customer.Email
        ORDER BY Total_Flights DESC
        LIMIT 1
    """

    cursor.execute(query_frequent, (airline_name,))
    frequent_customer = cursor.fetchone()

    # get all the customers whose 
    query_customers = """
        SELECT DISTINCT Customer.Email, Customer.First_Name, Customer.Last_Name
        FROM Ticket, Customer, Flight
        WHERE Flight.Airline_Name = %s
            AND Ticket.Email = Customer.Email
            AND Ticket.Flight_Num = Flight.Flight_Num
    """
    cursor.execute(query_customers, (airline_name,))
    customers = cursor.fetchall()

    flight_data = []
    for customer in customers:
        email = customer['Email']
        # getting the flight info for customers whose flight had passed 
        query_flights = """
            SELECT Flight.Flight_Num, Flight.Departure_Date, Flight.Arrival_Date, 
                Flight.Departure_Code, Flight.Arrival_Code
            FROM Ticket, Flight
            WHERE Ticket.Email = %s 
                AND Flight.Airline_Name = %s
                AND Ticket.Flight_Num = Flight.Flight_Num
                AND (
                    Flight.Departure_Date < CURDATE() OR 
                    (Flight.Departure_Date = CURDATE() AND Flight.Departure_Time < CURTIME())
                )
        """
        cursor.execute(query_flights, (email, airline_name))
        flights = cursor.fetchall()
        flight_data.append({'customer': customer, 'flights': flights})

    cursor.close()    
    if not frequent_customer:
        return "No frequent customers found in the last year."
    return render_template('view_frequent_customer.html', most_frequent_customer=frequent_customer,
            customer_flights_data=flight_data, airline_name=airline_name
    )

# use case 2, creating a flight. make sure airplane and airport exists and are associated with the airline
@app.route('/create_flight', methods=['GET', 'POST'])
def create_flight():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        # get the airline name the staff works at
        query_airline = 'SELECT Airline_Name FROM Works_For WHERE Username = %s'
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."

        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            flight_num = request.form.get('flight_num')
            departure_date = request.form.get('departure_date')
            departure_time = request.form.get('departure_time')
            arrival_date = request.form.get('arrival_date')
            arrival_time = request.form.get('arrival_time')
            base_ticket_price = request.form.get('base_ticket_price')
            flight_status = request.form.get('flight_status')
            airplane_id = request.form.get('airplane_id')
            departure_code = request.form.get('departure_code')
            arrival_code = request.form.get('arrival_code')

            if not ([flight_num and departure_date and departure_time and arrival_date and arrival_time, 
                        base_ticket_price and flight_status and airplane_id and departure_code and arrival_code]):
                return "Fill out all fields."

            try:
                conn.begin()
                # check for airplane existence within the airline
                query_airplane = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_airplane, (airplane_id, airline_name))
                airplane = cursor.fetchone()

                if not airplane:
                    return "Airplane not found."
                
                # check to see if airplane in going through maintenance during the flight
                query_maintenance = """
                    SELECT * 
                    FROM Maintenance_Procedure
                    WHERE Airplane_ID = %s 
                      AND Airline_Name = %s 
                      AND (
                        (%s BETWEEN Start_Date AND End_Date)
                        OR (%s BETWEEN Start_Date AND End_Date)
                        OR (Start_Date = %s AND Start_Time < %s)
                        OR (End_Date = %s AND End_Time > %s)
                      )
                """
                cursor.execute(query_maintenance, (airplane_id, airline_name, departure_date, arrival_date, 
                departure_date, departure_time, arrival_date, arrival_time))
                maintenance = cursor.fetchone()

                if maintenance:
                    return "The airplane is under maintenance during the given flight time."

                # check arrival and departure airports to see if they exist
                query_airport = "SELECT * FROM Airport WHERE Airport_Code = %s"
                cursor.execute(query_airport, (departure_code,))
                departure_airport = cursor.fetchone()
                cursor.execute(query_airport, (arrival_code,))
                arrival_airport = cursor.fetchone()
                if not departure_airport:
                    return "Departure airport does not exist."
                if not arrival_airport:
                    return "Arrival airport does not exist."

                # ensure that the airline operates at the given departure and arrival airports
                query_operates = """
                    SELECT * 
                    FROM Operates 
                    WHERE Airline_Name = %s AND Airport_Code = %s
                """
                cursor.execute(query_operates, (airline_name, departure_code))
                departure = cursor.fetchone()
                cursor.execute(query_operates, (airline_name, arrival_code))
                arrival = cursor.fetchone()

                if not departure:
                    return "Airline does not operate at departure airport."
                if not arrival:
                    return "Airline does not operate at arrival airport."

                # create the flight through insertion into flight
                query_insert = """
                    INSERT INTO Flight (Flight_Num, Departure_Date, Departure_Time, Arrival_Date, 
                                    Arrival_Time, Base_Ticket_Price, Flight_Status, Airline_Name, 
                                    Departure_Code, Arrival_Code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_insert, 
                    (flight_num, departure_date, departure_time, arrival_date, arrival_time, 
                     base_ticket_price, flight_status, airline_name, departure_code, arrival_code))

                # get the number of seats (plane capacity) for the airplane that is being used for flight
                query_cap = """
                    SELECT Number_of_Seats 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name=%s
                """
                cursor.execute(query_cap, (airplane_id, airline_name))
                capacity = cursor.fetchone()['Number_of_Seats']

                # insert a seat number, flight num into seat_availability. Set is available to true
                # which is used during purchasing of tickets
                for seat in range(1, capacity + 1):
                    seat_number = str(seat)
                    query_seat = """
                        INSERT INTO Seat_Availability (Flight_Num, Seat_Number, Is_Available)
                        VALUES (%s, %s, TRUE)
                    """
                    cursor.execute(query_seat, (flight_num, seat_number))
                conn.commit()
                return render_template('future_flights.html') # confirmation message for sucessful flight creation

            except Exception as e:
                conn.rollback()
                return f"Unable to create flight. {str(e)}"
            
        # display the future flights (for next 30 days)    
        query_future_flights = """
                    SELECT Flight_Num, Departure_Date, Departure_Time, Arrival_Date, Arrival_Time, Flight_Status
                    FROM Flight
                    WHERE Airline_Name = %s 
                    AND (
                        (Departure_Date BETWEEN CURDATE() AND CURDATE() + INTERVAL 30 DAY) OR
                        (Departure_Date = CURDATE() AND Departure_Time > CURTIME())
                    )
                """
        cursor.execute(query_future_flights, (airline_name,))
        flights = cursor.fetchall()

        return render_template('create_flight.html', flights=flights, airline_name=airline_name)

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()

@app.route('/schedule_maintenance', methods=['GET', 'POST'])
def schedule_maintenance():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    try:
        query_airline = "SELECT Airline_Name FROM Works_For WHERE Username = %s"
        cursor.execute(query_airline, (username,))
        staff_airline = cursor.fetchone()

        if not staff_airline:
            cursor.close()
            return "Airline for Airline Staff Not Found."
        airline_name = staff_airline['Airline_Name']

        if request.method == 'POST':
            airplane_id = request.form.get('airplane_id')
            start_date = request.form.get('start_date')
            start_time = request.form.get('start_time')
            end_date = request.form.get('end_date')
            end_time = request.form.get('end_time')

            if not ([airplane_id and start_date and start_time and end_date and end_time]):
                return "Fill out all fields."

            try:
                # make sure the airplane exists and belongs to the correct airline
                query_airplane = """
                    SELECT * 
                    FROM Airplane 
                    WHERE Airplane_ID = %s AND Airline_Name = %s
                """
                cursor.execute(query_airplane, (airplane_id, airline_name))
                airplane = cursor.fetchone()

                if not airplane:
                    return "Given airplane was not found."

                # looking for existing maintenenace procedure at the same time
                query_maintenance = """
                    SELECT * 
                    FROM Maintenance_Procedure
                    WHERE Airplane_ID = %s 
                      AND Airline_Name = %s 
                      AND (
                        (%s BETWEEN Start_Date AND End_Date) 
                        OR (%s BETWEEN Start_Date AND End_Date)
                      )
                """
                cursor.execute(query_maintenance, (airplane_id, airline_name, start_date, end_date))
                existing = cursor.fetchone()

                if existing:
                    return "Airplane is already scheduled for maintenance during the given dates."

                # insert into maintenance procedure
                query_insert_maintenance = """
                    INSERT INTO Maintenance_Procedure (
                        Airline_Name, Airplane_ID, Start_Date, Start_Time, End_Date, End_Time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query_insert_maintenance, (airline_name, airplane_id, start_date, start_time, 
                                                          end_date, end_time))
                conn.commit()

            except Exception as e:
                conn.rollback()
                return f"Unable to schedule maintenance: {str(e)}"

        return render_template('schedule_maintenance.html', airline_name=airline_name)
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()

# adding additional emails and phones for airline staff
# can provide either an email or a phone or both
@app.route('/add_staff_contact', methods=['GET', 'POST'])
def add_staff_contact():
    if 'role' not in session or session['role'] != 'staff':
        return redirect(url_for('login', role='staff'))
    
    username = session['username']
    cursor = conn.cursor()

    if request.method == 'POST':
        email = request.form.get('email')
        phone = request.form.get('phone')

        try:
            if email:
                # insert into email table
                query_email = """
                        INSERT INTO Airline_Staff_Email (Username, Email)
                        VALUES (%s, %s)
                    """
                cursor.execute(query_email, (username, email))
            
            # insert into phone table
            if phone: 
                query_phone = """
                        INSERT INTO Airline_Staff_Phone (Username, Phone)
                        VALUES (%s, %s)
                    """    
                cursor.execute(query_phone, (username, phone))
            conn.commit()

        except Exception as e:
            conn.rollback()
            return "error occuered"
        finally:
            cursor.close()
    return render_template('add_staff_contact.html')    


# Logout route 
@app.route('/logout')
def logout():
    role = session.get('role')
    session.pop('email', None)
    session.pop('username', None)
    session.pop('role', None)
    session.pop('first_name', None)

    if role == 'customer':
        return redirect(url_for('login', role='customer'))
    elif role == 'staff':
        return redirect(url_for('login', role='staff'))
    else:
        return redirect(url_for('hello'))

app.secret_key = 'some key that you will never guess'

# Run the app on localhost port 5000
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug=True)