# End-to-End Testing Guide

## Test Execution Plan

### Phase 1: User Registration & Authentication
1. ✓ Open landing page - verify ShopEase branding
2. ✓ Register new user (test1@example.com / testuser123 / testpass)
3. ✓ Login with registered credentials
4. ✓ Verify auth token in localStorage
5. ✓ Verify cart count updates after login
6. ✓ Visit /orders page with valid token
7. ✓ Visit /admin page - should be denied (non-admin user)

### Phase 2: Product Browsing & Search
1. ✓ Navigate to /store
2. ✓ View all products initially
3. ✓ Test search filter (search for "phone" or "shirt")
4. ✓ Test category filter (Electronics, Fashion, etc.)
5. ✓ Test price range filter (min: 50, max: 500)
6. ✓ Verify product grid updates correctly
7. ✓ Click "View Details" modal - check product info
8. ✓ Close modal without adding to cart

### Phase 3: Cart Operations - Real API Cart
1. ✓ Add product to cart from store page
2. ✓ Verify cart count badge updates
3. ✓ Add another product
4. ✓ Open cart panel in mini-sidebar
5. ✓ Verify cart shows correct items and quantities
6. ✓ Verify subtotal calculation is correct
7. ✓ Remove one item from cart
8. ✓ Verify cart updates immediately
9. ✓ Verify API cart persists across page reloads
10. ✓ Test adding same product twice - should increment quantity

### Phase 4: Wishlist Flow
1. ✓ Add product to wishlist from store
2. ✓ Verify wishlist count updates
3. ✓ Open wishlist panel
4. ✓ Move wishlist item to cart (quantity: 1)
5. ✓ Verify item appears in cart
6. ✓ Verify item removed from wishlist
7. ✓ Remove remaining wishlist items

### Phase 5: Coupon System
1. ✓ Create admin user for coupon testing (optional)
2. ✓ At checkout, enter invalid coupon - verify error
3. ✓ Enter valid coupon "SAVE10" (if exists in seed data)
4. ✓ Verify discount calculation: discount = total * (percent/100)
5. ✓ Verify final price = total - discount
6. ✓ Verify coupon can't be used twice (if max_uses=1)

### Phase 6: Checkout & Order Creation
1. ✓ With items in cart, click "Checkout"
2. ✓ Verify cart clears after checkout
3. ✓ Verify order appears in order history
4. ✓ Verify order has correct items and total price
5. ✓ Verify product stock decremented in DB
6. ✓ Verify order status = "pending"

### Phase 7: Order History & Tracking
1. ✓ Navigate to /orders page
2. ✓ Verify all orders listed for current user
3. ✓ Verify each order shows: ID, status, items, total price
4. ✓ Click "Track" button (📦) on an order
5. ✓ Verify shipment modal opens
6. ✓ Verify shipment timeline displays correctly
7. ✓ If no shipments exist, verify "No shipments" message

### Phase 8: Admin Dashboard
1. ✓ Login as admin user (see seed data)
2. ✓ Navigate to /admin
3. ✓ Verify admin auth modal if not logged in
4. ✓ Verify sales summary stats display
5. ✓ Verify best sellers list shows top 10 products
6. ✓ Verify order management table loads all orders
7. ✓ Verify product management table shows all products
8. ✓ Verify can edit product stock (type new number)
9. ✓ Verify can toggle "Featured" checkbox
10. ✓ Verify changes persist after page reload

### Phase 9: Admin - Shipment Management
1. ✓ In admin order table, find an order
2. ✓ Click "Manage Shipments" (if available)
3. ✓ Add new shipment with status: "processing" / "shipped" / "delivered"
4. ✓ Add location and notes
5. ✓ Verify shipment appears in timeline on customer /orders page
6. ✓ Verify shipment email is sent (check logs or mock SMTP)

### Phase 10: Data Consistency & Edge Cases
1. ✓ Double-add same product to cart - verify quantity increments, not duplicates
2. ✓ Add product, try checkout with insufficient stock - verify error
3. ✓ Create order with coupon, verify discount persists in order
4. ✓ Logout and login again - verify cart still there (user-specific)
5. ✓ Different user logs in - verify sees own cart only
6. ✓ Logout user A, login user B, verify user A's cart not visible
7. ✓ Check product reviews (if reviews exist)

### Phase 11: UI/UX & Error Handling
1. ✓ Try checkout with empty cart - verify error message
2. ✓ Try accessing order history as guest (no token) - verify denied
3. ✓ Try accessing admin page as non-admin - verify denied
4. ✓ Verify toast/notification messages appear correctly
5. ✓ Verify loading spinners appear during API calls
6. ✓ Test mobile menu toggle on small screens

### Phase 12: API Documentation
1. ✓ Navigate to /docs (Swagger UI)
2. ✓ Verify all endpoints are documented
3. ✓ Test an endpoint with Swagger (e.g., GET /products)
4. ✓ Verify auth token can be added in Swagger

## Success Criteria
- ✓ No console errors
- ✓ No API 500 errors
- ✓ Cart data persists correctly
- ✓ Orders created with accurate stock deduction
- ✓ Coupons apply correctly
- ✓ Admin features work as expected
- ✓ Shipment tracking displays properly
- ✓ User data is properly isolated

## Known Issues (Before Testing)
- None currently documented

## Issues Found During Testing
(To be updated as testing progresses)
