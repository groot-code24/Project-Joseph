CREATE TABLE IF NOT EXISTS customers (
  customer_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  tier TEXT NOT NULL CHECK(tier IN ('standard','vip','new')),
  phone TEXT,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  order_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL REFERENCES customers(customer_id),
  product_name TEXT NOT NULL,
  product_category TEXT NOT NULL,
  order_date TEXT NOT NULL,
  amount_usd REAL NOT NULL,
  payment_method TEXT NOT NULL,
  is_final_sale INTEGER NOT NULL DEFAULT 0,
  is_digital_good INTEGER NOT NULL DEFAULT 0,
  days_since_delivery INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL CHECK(status IN ('delivered','shipped','processing')),
  is_defective INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS refund_requests (
  request_id TEXT PRIMARY KEY,
  order_id TEXT NOT NULL REFERENCES orders(order_id),
  customer_id TEXT NOT NULL REFERENCES customers(customer_id),
  reason TEXT,
  requested_at TEXT DEFAULT (datetime('now')),
  status TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','denied','escalated_human')),
  resolution TEXT,
  resolved_by TEXT,
  resolved_at TEXT
);

INSERT OR IGNORE INTO customers (customer_id, name, email, tier, phone) VALUES
  ('CUS-001', 'Aaron Mitchell',   'aaron.mitchell@example.com',   'standard', '+1-202-555-0111'),
  ('CUS-002', 'Bianca Rossi',     'bianca.rossi@example.com',     'vip',      '+1-202-555-0112'),
  ('CUS-003', 'Chen Wei',         'chen.wei@example.com',         'new',      '+1-202-555-0113'),
  ('CUS-004', 'Diana Okafor',     'diana.okafor@example.com',     'standard', '+1-202-555-0114'),
  ('CUS-005', 'Ethan Brooks',     'ethan.brooks@example.com',     'vip',      '+1-202-555-0115'),
  ('CUS-006', 'Farah Haddad',     'farah.haddad@example.com',     'standard', '+1-202-555-0116'),
  ('CUS-007', 'Gabriel Santos',   'gabriel.santos@example.com',   'new',      '+1-202-555-0117'),
  ('CUS-008', 'Hannah Lieberman', 'hannah.lieberman@example.com', 'standard', '+1-202-555-0118'),
  ('CUS-009', 'Ivan Petrov',      'ivan.petrov@example.com',      'standard', '+1-202-555-0119'),
  ('CUS-010', 'Julia Fernandez',  'julia.fernandez@example.com',  'vip',      '+1-202-555-0120'),
  ('CUS-011', 'Kareem Nasser',    'kareem.nasser@example.com',    'standard', '+1-202-555-0121'),
  ('CUS-012', 'Lena Andersson',   'lena.andersson@example.com',   'new',      '+1-202-555-0122'),
  ('CUS-013', 'Marcus Reed',      'marcus.reed@example.com',      'standard', '+1-202-555-0123'),
  ('CUS-014', 'Nadia Khan',       'nadia.khan@example.com',       'vip',      '+1-202-555-0124'),
  ('CUS-015', 'Oscar Delgado',    'oscar.delgado@example.com',    'standard', '+1-202-555-0125');

INSERT OR IGNORE INTO orders
  (order_id, customer_id, product_name, product_category, order_date, amount_usd, payment_method, is_final_sale, is_digital_good, days_since_delivery, status, is_defective)
VALUES
  ('ORD-001', 'CUS-001', 'Aurora Desk Lamp',            'home',        '2026-05-26',  89.99, 'visa',       0, 0, 10, 'delivered',  0),
  ('ORD-002', 'CUS-002', 'Trailblazer Water Bottle',    'outdoor',     '2026-04-30',  45.00, 'mastercard', 0, 0, 35, 'delivered',  0),
  ('ORD-003', 'CUS-003', 'Clearance Wool Coat',         'apparel',     '2026-05-31', 120.00, 'visa',       1, 0,  5, 'delivered',  0),
  ('ORD-004', 'CUS-004', 'PixelForge Pro License',      'software',    '2026-06-04',  59.99, 'paypal',     0, 1,  2, 'delivered',  0),
  ('ORD-005', 'CUS-005', 'NovaSound Studio Monitors',   'electronics', '2026-05-29', 649.00, 'amex',       0, 0,  7, 'delivered',  0),
  ('ORD-006', 'CUS-010', 'Ergonomic Office Chair',      'furniture',   '2026-05-21', 210.00, 'visa',       0, 0, 15, 'delivered',  0),
  ('ORD-007', 'CUS-006', 'BlendMaster 9000 Mixer',      'kitchen',     '2026-05-16', 175.00, 'mastercard', 0, 0, 20, 'delivered',  1),
  ('ORD-008', 'CUS-007', 'Voyager Carry-On Suitcase',   'travel',      '2026-06-05',  99.00, 'visa',       0, 0,  0, 'shipped',    0),
  ('ORD-009', 'CUS-008', 'CozyKnit Throw Blanket',      'home',        '2026-06-07',  55.00, 'paypal',     0, 0,  0, 'processing', 0),
  ('ORD-010', 'CUS-005', 'HomeTheater Bundle Kit',      'electronics', '2026-05-28', 520.00, 'amex',       0, 0, 12, 'delivered',  1),
  ('ORD-011', 'CUS-011', 'Birthday Gift Hamper',        'gift',        '2026-05-24',  88.00, 'visa',       0, 0, 12, 'delivered',  0),
  ('ORD-012', 'CUS-009', 'SwiftStep Running Shoes',     'apparel',     '2026-05-28', 130.00, 'visa',       0, 0,  8, 'delivered',  0),
  ('ORD-013', 'CUS-013', 'Lumina Bedside Reader',       'home',        '2026-05-31', 149.00, 'mastercard', 0, 0,  5, 'delivered',  0),
  ('ORD-014', 'CUS-012', 'NovaRead E-Book Annual',      'software',    '2026-06-05',  29.99, 'paypal',     0, 1,  1, 'delivered',  0),
  ('ORD-015', 'CUS-014', 'Final Sale 4K Action Cam',    'electronics', '2026-06-03', 340.00, 'amex',       1, 0,  3, 'delivered',  0),
  ('ORD-016', 'CUS-001', 'Glacier Insulated Mug',       'outdoor',     '2026-05-18',  75.50, 'visa',       0, 0, 18, 'delivered',  0),
  ('ORD-017', 'CUS-015', 'ProGamer Mechanical Desk',    'furniture',   '2026-05-14', 610.00, 'mastercard', 0, 0, 22, 'delivered',  0),
  ('ORD-018', 'CUS-006', 'AeroPress Coffee Maker',      'kitchen',     '2026-05-22',  99.00, 'visa',       0, 0, 14, 'delivered',  1),
  ('ORD-019', 'CUS-004', 'Solstice Yoga Mat',           'fitness',     '2026-05-08',  42.00, 'paypal',     0, 0, 28, 'delivered',  0),
  ('ORD-020', 'CUS-008', 'Cascade Bluetooth Speaker',   'electronics', '2026-05-27', 199.00, 'visa',       0, 0,  9, 'delivered',  0),
  ('ORD-021', 'CUS-009', 'Trail Daypack 20L',           'outdoor',     '2026-04-26',  60.00, 'visa',       0, 0, 40, 'delivered',  0),
  ('ORD-022', 'CUS-009', 'Quartz Wall Clock',           'home',        '2026-04-16',  80.00, 'visa',       0, 0, 50, 'delivered',  0),
  ('ORD-023', 'CUS-009', 'Stainless Travel Flask',      'outdoor',     '2026-05-06',  70.00, 'visa',       0, 0, 30, 'delivered',  0),
  ('ORD-024', 'CUS-002', 'CloudSync Storage Plan',      'software',    '2026-06-03',  19.99, 'mastercard', 0, 1,  4, 'delivered',  0),
  ('ORD-025', 'CUS-014', 'Meridian Leather Wallet',     'accessories', '2026-06-01', 250.00, 'amex',       0, 0,  6, 'delivered',  0);

INSERT OR IGNORE INTO refund_requests
  (request_id, order_id, customer_id, reason, requested_at, status, resolution, resolved_by, resolved_at)
VALUES
  ('REQ-SEED-0001', 'ORD-020', 'CUS-008', 'Speaker stopped charging', datetime('now','-15 days'), 'approved', 'Approved within standard window per §1.', 'nova-ai', datetime('now','-15 days')),
  ('REQ-SEED-0002', 'ORD-021', 'CUS-009', 'Changed mind on color',    datetime('now','-10 days'), 'approved', 'Approved within standard window per §1.', 'nova-ai', datetime('now','-10 days')),
  ('REQ-SEED-0003', 'ORD-022', 'CUS-009', 'Found a cheaper option',   datetime('now','-20 days'), 'approved', 'Approved within standard window per §1.', 'nova-ai', datetime('now','-20 days')),
  ('REQ-SEED-0004', 'ORD-023', 'CUS-009', 'No longer needed',         datetime('now','-30 days'), 'approved', 'Approved within standard window per §1.', 'nova-ai', datetime('now','-30 days'));
