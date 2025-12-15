USE library_db;

DELIMITER //

-- Procedure to issue a book
-- Checks availability, decrements stock, creates transaction, sets due date (14 days)
CREATE PROCEDURE IF NOT EXISTS issue_book(IN p_user_id INT, IN p_book_id INT)
BEGIN
    DECLARE v_available INT;
    
    -- Check availability
    SELECT available_copies INTO v_available FROM books WHERE book_id = p_book_id;
    
    IF v_available > 0 THEN
        -- Decrease copy count
        UPDATE books SET available_copies = available_copies - 1 WHERE book_id = p_book_id;
        
        -- Insert Transaction with due date + 14 days
        INSERT INTO transactions (user_id, book_id, borrow_date, due_date)
        VALUES (p_user_id, p_book_id, CURRENT_DATE, DATE_ADD(CURRENT_DATE, INTERVAL 14 DAY));
    ELSE
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Book not available';
    END IF;
END //

-- Procedure to return a book
-- Updates return date, calculates fine if overdue, increments stock
CREATE PROCEDURE IF NOT EXISTS return_book(IN p_transaction_id INT)
BEGIN
    DECLARE v_due_date DATE;
    DECLARE v_return_date DATE;
    DECLARE v_days_overdue INT;
    DECLARE v_fine DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_book_id INT;
    
    SELECT due_date, book_id INTO v_due_date, v_book_id FROM transactions WHERE transaction_id = p_transaction_id;
    
    SET v_return_date = CURRENT_DATE;
    
    -- Calculate fine: $1 per day overdue
    IF v_return_date > v_due_date THEN
        SET v_days_overdue = DATEDIFF(v_return_date, v_due_date);
        SET v_fine = v_days_overdue * 1.00;
    END IF;
    
    -- Update transaction
    UPDATE transactions 
    SET return_date = v_return_date, 
        fine_amount = v_fine, 
        status = 'returned'
    WHERE transaction_id = p_transaction_id;
    
    -- Increase available copies
    UPDATE books SET available_copies = available_copies + 1 WHERE book_id = v_book_id;
    
END //

DELIMITER ;
