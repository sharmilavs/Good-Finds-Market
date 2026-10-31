from db import init_mongo, mongo

# Product format:
# (product_id, name, description, price_in_cents, available_stock, display_tone)
# Prices are stored in cents because the frontend uses price_cents.
PRODUCTS = [
    # Original products
    ("p-kettle", "Gooseneck Kettle", "1 L stainless kettle with a fine pour spout.", 5900, 25, "#2F4858"),
    ("p-grinder", "Hand Burr Grinder", "Steel burrs, 30 click settings, fits a travel bag.", 8900, 15, "#7A5C3E"),
    ("p-dripper", "Ceramic Dripper", "Cone dripper for a clean one-cup brew.", 3200, 40, "#C8B79E"),
    ("p-scale", "Brew Scale", "0.1 g precision with a built-in timer.", 4500, 20, "#3E5C4B"),
    ("p-server", "Glass Server 600 ml", "Heat-safe carafe with measuring marks.", 2400, 30, "#8AA6A3"),
    ("p-filters", "Paper Filters, 100", "Unbleached cone filters, size 02.", 800, 200, "#B5835A"),

    # Additional coffee products
    ("p-french-press", "French Press 800 ml", "Classic borosilicate glass press with a stainless-steel filter.", 3499, 35, "#8AA6A3"),
    ("p-moka-pot", "Stovetop Moka Pot", "Aluminium stovetop coffee maker for rich, espresso-style coffee.", 4299, 22, "#7A5C3E"),
    ("p-aeropress", "Aero Press Coffee Maker", "Compact manual coffee maker for smooth coffee at home or while travelling.", 3999, 18, "#C8B79E"),
    ("p-cold-brew", "Cold Brew Coffee Maker", "Glass cold-brew bottle with a reusable fine-mesh filter.", 2999, 28, "#2F4858"),
    ("p-electric-kettle", "Electric Kettle 1.5 L", "Fast-boil electric kettle with an automatic shut-off feature.", 4599, 16, "#3E5C4B"),
    ("p-travel-mug", "Insulated Travel Mug", "Double-wall mug designed to keep your coffee warm on the go.", 1899, 50, "#B5835A"),
    ("p-ceramic-mug", "Ceramic Coffee Mug", "Comfortable everyday mug with a 350 ml capacity.", 1299, 65, "#C8B79E"),
    ("p-bean-canister", "Coffee Bean Canister", "Airtight storage canister to help keep coffee beans fresh.", 2199, 32, "#7A5C3E"),
    ("p-milk-frother", "Handheld Milk Frother", "Battery-powered whisk for making creamy milk foam.", 1599, 40, "#8AA6A3"),
    ("p-tamper", "Espresso Coffee Tamper", "Solid coffee tamper for evenly compressing espresso grounds.", 2499, 24, "#2F4858"),
    ("p-knock-box", "Espresso Knock Box", "Countertop container for clean and easy disposal of used coffee grounds.", 2799, 14, "#3E5C4B"),
    ("p-server-large", "Glass Server 1 L", "Large heat-resistant glass server for sharing freshly brewed coffee.", 3299, 19, "#8AA6A3"),
    ("p-filter-metal", "Reusable Metal Filter", "Washable stainless-steel filter as an alternative to paper filters.", 1499, 45, "#B5835A"),
    ("p-filter-cloth", "Reusable Cloth Filters, 5", "Reusable cotton filters for a clean and balanced cup.", 999, 60, "#C8B79E"),
    ("p-cleaning-brush", "Coffee Equipment Cleaning Brush", "Small cleaning brush for grinders, drippers and coffee accessories.", 699, 80, "#7A5C3E"),
    ("p-bean-scoop", "Coffee Bean Measuring Scoop", "Stainless-steel scoop for measuring coffee beans and grounds.", 899, 55, "#2F4858"),
    ("p-pour-over-set", "Pour Over Starter Set", "Starter set with a dripper, server and measuring scoop.", 5499, 12, "#3E5C4B"),
    ("p-espresso-cups", "Espresso Cups, Set of 2", "Pair of small ceramic cups for serving espresso.", 1699, 26, "#B5835A"),
    # Additional marketplace products across everyday categories
    ("p-headphones", "Wireless Bluetooth Headphones", "Comfortable over-ear headphones with clear sound and long battery life.", 4999, 30, "#8AA6A3", "Electronics"),
    ("p-speaker", "Portable Bluetooth Speaker", "Compact wireless speaker for music at home or outdoors.", 2999, 25, "#2F4858", "Electronics"),
    ("p-smartwatch", "Fitness Smart Watch", "Everyday smartwatch with activity tracking and message alerts.", 6999, 18, "#3E5C4B", "Electronics"),
    ("p-powerbank", "20000 mAh Power Bank", "High-capacity portable charging for phones and accessories.", 2499, 40, "#7A5C3E", "Electronics"),
    ("p-desk-lamp", "Minimal LED Desk Lamp", "Adjustable reading lamp with soft, eye-friendly lighting.", 1899, 32, "#C8B79E", "Home & Living"),
    ("p-planter", "Ceramic Indoor Planter", "Modern ceramic planter for desks, shelves and windowsills.", 899, 45, "#8AA6A3", "Home & Living"),
    ("p-bedsheet", "Cotton Bedsheet Set", "Soft double-bed cotton bedsheet set with matching pillow covers.", 2199, 20, "#B5835A", "Home & Living"),
    ("p-backpack", "Everyday Laptop Backpack", "Lightweight backpack with padded laptop compartment and organizer pockets.", 2799, 22, "#2F4858", "Fashion"),
    ("p-wallet", "Classic Everyday Wallet", "Slim wallet with multiple card slots and a compact design.", 1199, 35, "#7A5C3E", "Fashion"),
    ("p-sneakers", "Casual Everyday Sneakers", "Versatile lightweight sneakers for daily wear.", 3499, 16, "#C8B79E", "Fashion"),
    ("p-sunscreen", "Daily SPF 50 Sunscreen", "Lightweight broad-spectrum sunscreen for everyday use.", 799, 50, "#B5835A", "Beauty"),
    ("p-moisturizer", "Hydrating Face Moisturizer", "Gentle daily moisturizer for soft, hydrated skin.", 699, 42, "#8AA6A3", "Beauty"),
    ("p-notebook", "Premium Ruled Notebook", "Hardcover notebook for notes, planning and journaling.", 499, 80, "#3E5C4B", "Books"),
    ("p-yogamat", "Non-Slip Yoga Mat", "Comfortable exercise mat for yoga, stretching and home workouts.", 1499, 28, "#7A5C3E", "Fitness"),
    ("p-resistance", "Resistance Bands Set", "Multi-level resistance bands for strength and mobility workouts.", 999, 34, "#2F4858", "Fitness"),
    ("p-fiction-novel", "The Silent Library", "A mystery novel about secrets hidden inside an old town library.", 399, 60, "#7A5C3E", "Books"),
    ("p-romance-novel", "Letters in the Rain", "A heartwarming contemporary romance about friendship and second chances.", 449, 45, "#B5835A", "Books"),
    ("p-python-book", "Python Programming for Beginners", "A beginner-friendly guide to Python fundamentals, examples and practice problems.", 599, 40, "#2F4858", "Books"),
    ("p-java-book", "Java: A Practical Introduction", "Learn Java syntax, object-oriented programming and basic application development.", 699, 35, "#3E5C4B", "Books"),
    ("p-cybersecurity-book", "Introduction to Cybersecurity", "An accessible introduction to networks, online threats and defensive security practices.", 749, 30, "#2F4858", "Books"),
    ("p-datascience-book", "Data Science Essentials", "A practical introduction to data analysis, visualisation and machine learning concepts.", 799, 28, "#8AA6A3", "Books"),
    ("p-dbms-book", "Database Management Systems", "Understand relational databases, SQL, data modelling and transactions.", 649, 32, "#7A5C3E", "Books"),
    ("p-selfhelp-book", "Small Habits, Big Changes", "A practical personal-development book about building consistent daily habits.", 499, 50, "#C8B79E", "Books"),
    ("p-biography-book", "Beyond the Finish Line", "An inspiring biography about resilience, ambition and personal achievement.", 549, 25, "#B5835A", "Books"),
    ("p-travel-book", "The Art of Slow Travel", "A travel guide encouraging thoughtful journeys, local discovery and mindful exploration.", 599, 22, "#8AA6A3", "Books"),
    ("p-cookbook", "Everyday Home Cooking", "A collection of simple recipes and useful kitchen tips for everyday meals.", 499, 38, "#3E5C4B", "Books"),
    ("p-notes-journal", "Daily Planner & Journal", "A dated-free planner with space for goals, notes, priorities and reflections.", 349, 75, "#C8B79E", "Books"),
]


def main():
    init_mongo()
    for product in PRODUCTS:
        # Older coffee products have 6 fields; marketplace products also
        # include a 7th field containing their category.
        pid, name, desc, price, stock, tone = product[:6]
        category = product[6] if len(product) > 6 else "Coffee & Kitchen"

        mongo.products.update_one(
            {"_id": pid},
            {
                "$set": {
                    "name": name,
                    "description": desc,
                    "price_cents": price,
                    "stock": stock,
                    "tone": tone,
                    "category": category,
                }
            },
            upsert=True,
        )
    print(f"Seeded/updated {len(PRODUCTS)} products.")


if __name__ == "__main__":
    main()
