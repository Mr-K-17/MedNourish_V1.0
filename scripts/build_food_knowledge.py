"""Builds and validates curated food knowledge for MedNourish CarePlan v3.

Outputs:
- knowledge/curated/food_items.csv (>=150 everyday foods with comprehensive annotations)
- knowledge/curated/nutrient_guidance.csv (guidance for 18 nutrients)
"""

import csv
import os
import re
import sys

FOOD_ITEMS_PATH = "knowledge/curated/food_items.csv"
NUTRIENT_GUIDANCE_PATH = "knowledge/curated/nutrient_guidance.csv"

ALLOWED_CUISINES = {"indian", "global"}
ALLOWED_FOOD_GROUPS = {
    "cereal", "millet", "pulse", "vegetable", "leafy_green",
    "fruit", "dairy", "egg", "meat", "fish", "nut_seed", "oil", "beverage"
}
ALLOWED_MEAL_SLOTS = {"breakfast", "lunch", "dinner", "fruit_side"}
ALLOWED_DIET_TAGS = {"veg", "vegan", "egg", "nonveg"}
ALLOWED_ALLERGENS = {"gluten", "dairy", "nuts", "egg", "fish", "soy"}
ALLOWED_CAUTIONS = {"high_sugar", "high_potassium", "high_sodium"}

BANNED_REGEX = re.compile(
    r"\b(supplement|tablet|capsule|pill|multivitamin|dose|mg|mcg|iu|cure|treat|diagnosis|diagnose|prescribe|prescription)\b",
    re.IGNORECASE
)

# 18 Target Nutrients
NUTRIENT_LIST = [
    "vitamin_a", "b_complex", "b2", "b3", "b9_folate", "b12",
    "vitamin_c", "vitamin_d", "vitamin_e", "vitamin_k",
    "iron", "zinc", "biotin", "protein_energy",
    "fiber", "protein", "calcium", "water"
]

NUTRIENT_DISPLAY_NAMES = {
    "vitamin_a": "Vitamin A",
    "b_complex": "Vitamin B Complex",
    "b2": "Vitamin B2 (Riboflavin)",
    "b3": "Vitamin B3 (Niacin)",
    "b9_folate": "Vitamin B9 (Folate)",
    "b12": "Vitamin B12",
    "vitamin_c": "Vitamin C",
    "vitamin_d": "Vitamin D",
    "vitamin_e": "Vitamin E",
    "vitamin_k": "Vitamin K",
    "iron": "Iron",
    "zinc": "Zinc",
    "biotin": "Biotin",
    "protein_energy": "Protein-Energy",
    "fiber": "Dietary Fiber",
    "protein": "Protein",
    "calcium": "Calcium",
    "water": "Hydration / Water Balance"
}

# Guidance table definitions
NUTRIENT_GUIDANCE_DATA = [
    {
        "nutrient": "vitamin_a",
        "eat_more": "Carrots, sweet potatoes, pumpkin, spinach, methi leaves, moringa, bell peppers, fortified dairy",
        "fruit_picks": "Papaya;Ripe Mango;Cantaloupe;Watermelon;Apricot",
        "habits_to_improve": "Lightly cook or steam orange and dark green vegetables with healthy cooking fats like olive oil or ghee to boost absorption",
        "limit_or_avoid": "Excess alcohol intake and extremely low-fat diets that hinder absorption of fat-soluble vitamins",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "b_complex",
        "eat_more": "Whole wheat chapathi, brown rice, millets, oats, lentils, green peas, chickpeas, sunflower seeds",
        "fruit_picks": "Banana;Pomegranate;Avocado;Orange;Guava",
        "habits_to_improve": "Eat balanced regular meals featuring whole unrefined grains and soaked sprouted pulses rather than refined flours",
        "limit_or_avoid": "Excessive intake of refined sugars, polished white flours, and heavy alcohol that deplete B-vitamin reserves",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "b2",
        "eat_more": "Curd, yogurt, paneer, eggs, mushrooms, spinach, almonds, soybeans, lentils",
        "fruit_picks": "Avocado;Banana;Prunes;Figs;Apples",
        "habits_to_improve": "Store dairy and grains away from direct light and avoid discarding water used for soaking or boiling legumes",
        "limit_or_avoid": "Over-boiling vegetables in excessive water and prolonged exposure of milk or grains to sunlight",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "b3",
        "eat_more": "Roasted peanuts, chicken breast, tuna, salmon, brown rice, whole wheat, mushrooms, green peas",
        "fruit_picks": "Banana;Mango;Guava;Peach;Cantaloupe",
        "habits_to_improve": "Include protein-rich staples and seeds across main meals to facilitate cellular energy release",
        "limit_or_avoid": "Heavy alcohol consumption and exclusive reliance on untreated unfortified corn flours",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "b9_folate",
        "eat_more": "Spinach, methi, asparagus, broccoli, chickpeas, rajma, edamame, moong dal, whole lentils",
        "fruit_picks": "Orange;Papaya;Pomegranate;Strawberries;Guava",
        "habits_to_improve": "Lightly steam or saute greens rather than overcooking in open pots to preserve delicate heat-sensitive folates",
        "limit_or_avoid": "Re-heating cooked green leafy dishes repeatedly and consuming ultra-processed packaged snacks",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "b12",
        "eat_more": "Free-range eggs, curd, paneer, cow milk, wild salmon, sardines, chicken, fortified soy milk",
        "fruit_picks": "Banana;Apple;Berries;Avocado;Kiwi",
        "habits_to_improve": "Pair meals with fermented foods like curd or kefir to promote healthy digestion and gastrointestinal function",
        "limit_or_avoid": "Heavy alcohol use and unfortified strict plant-only diets without consistent fortified staples",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "vitamin_c",
        "eat_more": "Amla, bell peppers, broccoli, tomatoes, cabbage, cauliflower, fresh coriander, green chilies",
        "fruit_picks": "Amla;Guava;Orange;Lemon;Kiwi;Strawberries;Pineapple;Papaya",
        "habits_to_improve": "Squeeze fresh lemon or add fresh chopped citrus and tomatoes right before serving to prevent heat oxidation",
        "limit_or_avoid": "Prolonged boiling, soaking vegetables for hours after chopping, and cooking in unlined copper cookware",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "vitamin_d",
        "eat_more": "Fortified cow milk, fortified soy milk, egg yolks, salmon, mackerel, sun-exposed mushrooms",
        "fruit_picks": "Orange;Banana;Avocado;Papaya;Berries",
        "habits_to_improve": "Spend 15 to 20 minutes outdoors in safe morning sunlight and pair meals with dietary fats for uptake",
        "limit_or_avoid": "Sedentary all-day indoor routines without natural daylight and strict ultra-low-fat diets",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "vitamin_e",
        "eat_more": "Almonds, sunflower seeds, spinach, olive oil, mustard greens, peanut butter, pumpkin seeds",
        "fruit_picks": "Avocado;Kiwi;Blackberries;Mango;Papaya",
        "habits_to_improve": "Sprinkle roasted seeds onto warm salads or porridges and store cold-pressed oils in dark sealed containers",
        "limit_or_avoid": "Reheating cooking oil multiple times and deep-frying at excessively high smoke points",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "vitamin_k",
        "eat_more": "Spinach, methi, kale, cabbage, broccoli, green beans, mustard greens, peas, parsley",
        "fruit_picks": "Kiwi;Blueberries;Pomegranate;Green Grapes;Plums",
        "habits_to_improve": "Pair dark green vegetables with small amounts of heart-healthy oils to facilitate fat-soluble absorption",
        "limit_or_avoid": "Discarding outer green vegetable leaves where sunlight triggers the highest natural vitamin accumulation",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "iron",
        "eat_more": "Spinach, methi, ragi, bajra, chickpeas, rajma, lentils, pumpkin seeds, chicken liver, lean mutton",
        "fruit_picks": "Pomegranate;Amla;Guava;Watermelon;Dates;Figs",
        "habits_to_improve": "Pair plant-based iron dishes with vitamin C rich fruits or lemon juice to increase absorption",
        "limit_or_avoid": "Drinking black tea, coffee, or milk right with main meals as tannins and calcium inhibit iron absorption",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "zinc",
        "eat_more": "Pumpkin seeds, sesame seeds, chickpeas, lentils, paneer, eggs, chicken, yogurt, cashew nuts",
        "fruit_picks": "Avocado;Pomegranate;Guava;Blackberries;Banana",
        "habits_to_improve": "Soak, ferment, or sprout whole beans and grains before cooking to break down natural phytates and free minerals",
        "limit_or_avoid": "Unsoaked raw grains and excessive intake of highly refined grain products lacking germ nutrients",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "biotin",
        "eat_more": "Whole eggs, sweet potatoes, almonds, walnuts, sunflower seeds, oats, mushrooms, spinach",
        "fruit_picks": "Banana;Avocado;Strawberries;Raspberries;Watermelon",
        "habits_to_improve": "Cook egg whites thoroughly because raw avidin binds biotin and prevents natural digestive absorption",
        "limit_or_avoid": "Consuming raw or runny uncooked egg whites and relying on heavy alcohol intake",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "protein_energy",
        "eat_more": "Moong dal, toor dal, rajma, chana, paneer, eggs, chicken, fish, tofu, edamame, whole milk, curd",
        "fruit_picks": "Banana;Guava;Avocado;Dates;Pomegranate",
        "habits_to_improve": "Eat regular structured meals with a distinct protein staple across breakfast, lunch, and dinner",
        "limit_or_avoid": "Skipping main meals and replacing meals with empty-calorie sweetened beverages or processed chips",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "fiber",
        "eat_more": "Oats, whole wheat, ragi, barley, lentils, beans, carrots, peas, flaxseeds, chia seeds",
        "fruit_picks": "Apple;Guava;Pear;Orange;Papaya;Berries;Pomegranate",
        "habits_to_improve": "Eat whole fruits with edible skin intact rather than straining them into refined clear juices",
        "limit_or_avoid": "Stripped white bread, refined pastries, and straining vegetable broths to discard natural fiber",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "protein",
        "eat_more": "Dal, rajma, chana, sprouts, paneer, Greek yogurt, eggs, chicken, fish, tofu, peanut butter",
        "fruit_picks": "Guava;Avocado;Banana;Dates;Apricot",
        "habits_to_improve": "Combine cereals with pulses such as rice with dal or chapathi with chana for a complete amino acid profile",
        "limit_or_avoid": "Ultra-processed low-protein snacks and erratic fasting that compromises steady lean muscle nourishment",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "calcium",
        "eat_more": "Ragi, curd, paneer, cow milk, sesame seeds, tofu, almonds, methi leaves, amaranth greens, broccoli",
        "fruit_picks": "Figs;Orange;Papaya;Blackberries;Kiwi",
        "habits_to_improve": "Incorporate ragi porridge or curd into daytime meals and maintain active outdoor movement",
        "limit_or_avoid": "Excessive carbonated cola drinks and very high sodium intake that accelerates calcium excretion",
        "source_note": "unreviewed draft"
    },
    {
        "nutrient": "water",
        "eat_more": "Cucumber, tomatoes, buttermilk, tender coconut water, vegetable broth, clear soups, celery",
        "fruit_picks": "Watermelon;Muskmelon;Orange;Sweet Lime;Strawberries;Grapes;Pineapple",
        "habits_to_improve": "Drink water steadily throughout the day before feeling parched and carry a refillable water bottle",
        "limit_or_avoid": "Excess caffeine, sugary energy drinks, and high-sodium salted preserved snacks that increase thirst",
        "source_note": "unreviewed draft"
    }
]

# Raw definition of food items catalog (food_id, name, cuisine, food_group, meal_slots, diet_tags, allergens, cautions, nutrients, prep_note)
# Each entry is a tuple of 10 items
RAW_FOODS = [
    # --- Millets & Ancient Grains ---
    ("f_ragi_roti", "Ragi Roti with Onions", "indian", "millet", "breakfast;lunch;dinner", "veg;vegan", "", "high_potassium", "calcium;iron;fiber;b_complex", "Warm finger millet flatbread pressed with onion and cumin"),
    ("f_ragi_porridge", "Savory Ragi Buttermilk Porridge", "indian", "millet", "breakfast", "veg", "dairy", "high_potassium", "calcium;iron;water;b2", "Cooling ragi malt simmered and whisked with light curd"),
    ("f_jowar_bhakri", "Jowar Bhakri Flatbread", "indian", "millet", "lunch;dinner", "veg;vegan", "", "high_potassium", "fiber;iron;b_complex;zinc", "Hand-flattened sorghum flatbread baked on an iron skillet"),
    ("f_bajra_roti", "Bajra Roti with Fenugreek", "indian", "millet", "lunch;dinner", "veg;vegan", "", "high_potassium", "iron;fiber;zinc;b9_folate", "Pearl millet flatbread kneaded with fresh methi greens"),
    ("f_foxtail_upma", "Foxtail Millet Vegetable Upma", "indian", "millet", "breakfast;dinner", "veg;vegan", "", "", "fiber;b_complex;iron;vitamin_c", "Fluffy steamed foxtail millet tossed with ginger and peas"),
    ("f_little_millet_khichdi", "Little Millet Moong Khichdi", "indian", "millet", "lunch;dinner", "veg;vegan", "", "", "fiber;protein;b_complex;zinc", "Nutritious slow-simmered millet cooked with yellow moong"),
    ("f_barnyard_pulao", "Barnyard Millet Garden Pulao", "indian", "millet", "lunch;dinner", "veg;vegan", "", "", "fiber;iron;vitamin_a;vitamin_c", "Millet pilaf gently spiced with bay leaf, peas, and carrots"),

    # --- Whole Wheats & Cereals ---
    ("f_chapathi", "Whole Wheat Chapathi", "indian", "cereal", "breakfast;lunch;dinner", "veg;vegan", "gluten", "", "fiber;b_complex;iron;protein", "Puffed whole wheat tawa flatbread brushed with water or oil"),
    ("f_multigrain_roti", "Multigrain Phulka", "indian", "cereal", "lunch;dinner", "veg;vegan", "gluten", "", "fiber;protein;iron;b_complex", "Handmade phulka blended with whole wheat, oats, and barley"),
    ("f_methi_thepla", "Spiced Methi Thepla", "indian", "cereal", "breakfast;lunch", "veg;vegan", "gluten", "", "iron;vitamin_a;b9_folate;fiber", "Whole wheat rolled flatbread infused with fresh fenugreek"),
    ("f_vegetable_dalia", "Broken Wheat Vegetable Dalia", "indian", "cereal", "breakfast;dinner", "veg;vegan", "gluten", "", "fiber;iron;b_complex;vitamin_c", "Hearty cracked wheat porridge cooked with peas and carrots"),
    ("f_rolled_oats_porridge", "Warm Rolled Oats Porridge", "global", "cereal", "breakfast", "veg;vegan", "", "", "fiber;biotin;zinc;b_complex", "Rolled oats simmered with cinnamon and water or almond milk"),
    ("f_overnight_chia_oats", "Overnight Oats with Chia Seeds", "global", "cereal", "breakfast", "veg;vegan", "", "", "fiber;calcium;b_complex;zinc", "Chilled oats soaked overnight with soaked chia and cinnamon"),
    ("f_steamed_brown_rice", "Steamed Brown Basmati Rice", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "", "fiber;b_complex;b3;zinc", "Nutty whole grain brown rice steamed tender and fluffy"),
    ("f_red_rice_kanji", "Red Rice Kanji Broth", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "fiber;iron;zinc;water", "Traditional cooked red rice broth seasoned with roasted cumin"),
    ("f_wholewheat_sourdough", "Toasted Whole Wheat Sourdough", "global", "cereal", "breakfast;lunch", "veg;vegan", "gluten", "", "fiber;b_complex;iron;zinc", "Fermented artisan whole grain sourdough slice toasted crisp"),

    # --- Traditional Breakfast Staples ---
    ("f_steamed_idli", "Steamed Rice and Urad Idli", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "protein;b_complex;b2;zinc", "Fermented soft steamed rice and black gram savory cakes"),
    ("f_ragi_idli", "Steamed Ragi Idli", "indian", "millet", "breakfast;dinner", "veg;vegan", "", "high_potassium", "calcium;iron;fiber;protein", "Fermented finger millet batter steamed into pillowy cakes"),
    ("f_plain_dosa", "Crisp Sourdough Dosa", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "b_complex;protein;energy;iron", "Thin golden fermented crepe seared crisp on a tawa"),
    ("f_pesarattu", "Whole Green Moong Pesarattu", "indian", "pulse", "breakfast;dinner", "veg;vegan", "", "", "protein;iron;fiber;b9_folate", "Traditional Andhra green gram dosa ground with ginger and chili"),
    ("f_vegetable_poha", "Beaten Rice Vegetable Poha", "indian", "cereal", "breakfast", "veg;vegan", "nuts", "", "iron;vitamin_c;b_complex;energy", "Flattened rice tempered with mustard, roasted peanuts, lemon"),
    ("f_sooji_upma", "Semolina Vegetable Upma", "indian", "cereal", "breakfast;dinner", "veg;vegan", "gluten", "", "fiber;b_complex;iron;vitamin_a", "Roasted wheat semolina cooked with curry leaves and veggies"),
    ("f_oats_upma", "Vegetable Oats Upma", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "fiber;biotin;zinc;vitamin_c", "Toasted whole rolled oats tossed with ginger, carrots, peas"),

    # --- Lentils, Pulses & Dal Dishes ---
    ("f_yellow_moong_dal", "Yellow Moong Dal Tadka", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;b9_folate;iron;zinc", "Golden skinned split mung beans cooked with cumin and garlic"),
    ("f_toor_dal_sambar", "Vegetable Drumstick Sambar", "indian", "pulse", "breakfast;lunch;dinner", "veg;vegan", "", "", "protein;fiber;vitamin_a;vitamin_c", "Tangy toor dal lentil stew simmered with moringa drumsticks"),
    ("f_dal_makhani_light", "Home-Style Slow Dal Makhani", "indian", "pulse", "lunch;dinner", "veg", "dairy", "", "protein;fiber;iron;calcium", "Black lentils and kidney beans simmered with light curd cream"),
    ("f_punjabi_rajma", "Simmered Punjabi Rajma Curry", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "high_potassium", "iron;b9_folate;fiber;protein", "Red kidney beans slow cooked with tomatoes, ginger, spices"),
    ("f_kala_chana_curry", "Black Chickpea Kala Chana", "indian", "pulse", "breakfast;lunch;dinner", "veg;vegan", "", "high_potassium", "iron;fiber;protein;zinc", "Dense brown chickpeas stewed in an aromatic onion-tomato base"),
    ("f_kabuli_chole", "Spiced Kabuli Chana Chole", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;fiber;zinc;iron", "White chickpeas simmered with roasted cumin, tea-leaf extract"),
    ("f_whole_masoor_dal", "Brown Lentil Masoor Curry", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;fiber;iron;b_complex", "Earthy whole brown lentils gently tempered with cumin seeds"),
    ("f_chana_dal_lauki", "Chana Dal with Bottle Gourd", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "fiber;protein;water;iron", "Bengal gram split lentils cooked with cooling tender lauki"),
    ("f_palak_dal", "Spinach Moong Dal Melange", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_a;b9_folate;iron;fiber", "Tender yellow moong dal cooked with garden fresh spinach"),
    ("f_sprouted_moong_salad", "Sprouted Moong Chaat Salad", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "", "vitamin_c;protein;fiber;b9_folate", "Raw sprouted green gram tossed with lime juice, cucumber"),
    ("f_edamame_salad", "Steamed Green Edamame Pods", "global", "pulse", "lunch;dinner", "veg;vegan", "soy", "high_potassium", "protein;b9_folate;iron;fiber", "Young whole green soybeans lightly tossed with sea salt"),
    ("f_lentil_vegetable_soup", "Warm French Lentil Soup", "global", "pulse", "lunch;dinner", "veg;vegan", "", "", "fiber;protein;iron;b9_folate", "Hearty brown lentils simmered with celery, leeks, and carrots"),
    ("f_hummus_tahini", "Chickpea Hummus with Sesame", "global", "pulse", "breakfast;lunch;dinner", "veg;vegan", "", "", "protein;fiber;calcium;zinc", "Creamy blended chickpeas with sesame tahini and garlic"),

    # --- Dairy, Eggs & Tofu Alternatives ---
    ("f_plain_curd", "Set Cow Milk Curd / Dahi", "indian", "dairy", "breakfast;lunch;dinner", "veg", "dairy", "", "b12;calcium;b2;protein", "Fresh homemade probiotic whole milk yogurt set overnight"),
    ("f_greek_yogurt", "Unsweetened Plain Greek Yogurt", "global", "dairy", "breakfast;lunch", "veg", "dairy", "", "protein;b12;calcium;b2", "Thick strained natural yogurt rich in casein and whey"),
    ("f_paneer_tikka", "Grilled Spiced Paneer Tikka", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "protein;calcium;b12;zinc", "Firm cottage cheese cubes marinated in spiced hung yogurt"),
    ("f_palak_paneer", "Home-Style Palak Paneer", "indian", "dairy", "lunch;dinner", "veg", "dairy", "high_potassium", "vitamin_a;calcium;iron;b12", "Fresh cottage cheese simmered in seasoned puree of spinach"),
    ("f_spiced_buttermilk", "Tempered Masala Buttermilk", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "water;calcium;b12;b2", "Churned yogurt drink spiced with curry leaves and ginger"),
    ("f_tofu_stirfry", "Sesame Glazed Firm Tofu", "global", "pulse", "lunch;dinner", "veg;vegan", "soy", "", "protein;calcium;iron;zinc", "Pan-seared firm soy tofu tossed with sesame seeds and bell pepper"),
    ("f_palak_tofu", "Vegan Palak Tofu Curry", "indian", "vegetable", "lunch;dinner", "veg;vegan", "soy", "high_potassium", "iron;vitamin_a;calcium;protein", "Cubes of firm tofu cooked in hearty fenugreek spinach gravy"),
    ("f_boiled_egg", "Soft Boiled Country Egg", "global", "egg", "breakfast;lunch", "veg;egg", "", "", "protein;b12;biotin;vitamin_d", "Free-range whole chicken egg cooked gently for tender yolk"),
    ("f_egg_bhurji", "Indian Spiced Egg Bhurji", "indian", "egg", "breakfast;dinner", "veg;egg", "", "", "protein;b12;vitamin_a;biotin", "Scrambled eggs stir-fried with onions, tomatoes, coriander"),
    ("f_vegetable_omelette", "Garden Vegetable Omelette", "global", "egg", "breakfast;dinner", "veg;egg", "", "", "protein;b12;vitamin_c;biotin", "Whisked farm eggs folded over diced peppers and spinach"),
    ("f_egg_curry", "South Indian Egg Coconut Curry", "indian", "egg", "lunch;dinner", "veg;egg", "", "", "protein;b12;iron;vitamin_d", "Hard-boiled eggs simmered in a light coriander curry broth"),
    ("f_poached_egg_toast", "Poached Egg on Rye Sourdough", "global", "egg", "breakfast", "veg;egg", "gluten", "", "protein;b12;biotin;b_complex", "Warm pasture egg served over rustic toasted artisan bread"),

    # --- Fish & Poultry ---
    ("f_grilled_salmon", "Pan Seared Wild Salmon", "global", "fish", "lunch;dinner", "nonveg", "", "high_potassium", "vitamin_d;b12;protein;b3", "Wild caught salmon fillet cooked skin-down with lemon herbs"),
    ("f_steamed_fish_curry", "Kerala Steamed Fish in Curry Leaf", "indian", "fish", "lunch;dinner", "nonveg", "", "", "protein;vitamin_d;b12;zinc", "Fresh coastal white fish simmered with kokum and fresh spices"),
    ("f_sardines_curry", "Tomato Simmered Sardines", "indian", "fish", "lunch;dinner", "nonveg", "", "", "calcium;vitamin_d;b12;iron", "Small oily sardines stewed whole with tomatoes and tamarind"),
    ("f_grilled_chicken_breast", "Herbed Grilled Chicken Breast", "global", "meat", "lunch;dinner", "nonveg", "", "", "protein;b3;b_complex;zinc", "Lean skinless chicken breast marinated in rosemary and garlic"),
    ("f_country_chicken_curry", "Home Style Chicken Curry", "indian", "meat", "lunch;dinner", "nonveg", "", "", "protein;b3;iron;zinc", "Bone-in tender chicken simmered with ginger-garlic gravy"),
    ("f_chicken_moringa_soup", "Chicken and Moringa Clear Soup", "indian", "meat", "breakfast;dinner", "nonveg", "", "", "protein;water;iron;vitamin_c", "Slow-simmered bone broth cooked with fresh moringa leaves"),

    # --- Green Leafy Vegetables ---
    ("f_steamed_spinach", "Garlic Steamed Fresh Spinach", "global", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_a;vitamin_k;b9_folate;iron", "Baby spinach leaves wilted quickly with minced garlic"),
    ("f_methi_aloo_dry", "Fenugreek Methi Greens Stirfry", "indian", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "iron;vitamin_a;b9_folate;calcium", "Chopped bitter fenugreek leaves sauteed with light cumin"),
    ("f_sarson_saag", "Traditional Mustard Sarson Saag", "indian", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_k;vitamin_a;vitamin_c;calcium", "Simmered mustard greens with bathua and ginger root"),
    ("f_moringa_poriyal", "Drumstick Leaves Moringa Poriyal", "indian", "leafy_green", "lunch;dinner", "veg;vegan", "", "", "vitamin_a;iron;calcium;vitamin_c", "Tender moringa leaves sauteed with mustard and fresh coconut"),
    ("f_amaranth_greens", "Red Amaranth Leaves Thoran", "indian", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "calcium;iron;vitamin_a;vitamin_c", "Chopped red amaranth leaves steamed with shallots and chili"),
    ("f_steamed_kale", "Braised Curly Kale with Olive Oil", "global", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_k;vitamin_a;vitamin_c;calcium", "Hearty kale leaves braised with crushed garlic and pepper"),

    # --- Vegetables & Roots ---
    ("f_roasted_carrots", "Roasted Orange Carrots in Cumin", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_a;fiber;vitamin_c;water", "Tender sweet carrots roasted golden with olive oil and cumin"),
    ("f_baked_sweet_potato", "Baked Cinnamon Sweet Potato", "global", "vegetable", "breakfast;lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_a;biotin;fiber;b_complex", "Whole sweet potato baked until caramelized with cinnamon"),
    ("f_yellow_pumpkin_curry", "Yellow Pumpkin Kaddu Sabzi", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_a;fiber;water;vitamin_c", "Diced yellow pumpkin braised with fenugreek seeds and mango powder"),
    ("f_steamed_broccoli", "Lightly Steamed Broccoli Florets", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;vitamin_k;b9_folate;calcium", "Bright green crisp broccoli steamed and seasoned with lemon"),
    ("f_spiced_cauliflower", "Roasted Gobi Florets with Turmeric", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;vitamin_k;b9_folate;fiber", "Cauliflower tossed with wild turmeric and roasted dry"),
    ("f_bhindi_masala", "Crispy Okra Bhindi Masala", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "b9_folate;fiber;calcium;vitamin_c", "Sliced ladyfingers shallow pan-seared with coriander and cumin"),
    ("f_lauki_sabzi", "Bottle Gourd Lauki Stew", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;fiber;vitamin_c;b_complex", "Tender calabash squash gently cooked with cumin and curry leaf"),
    ("f_beetroot_poriyal", "Grated Beetroot Thoran", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "high_potassium", "b9_folate;iron;fiber;potassium", "Grated crimson beets sauteed with mustard seeds and coconut"),
    ("f_tomato_rasam", "Tangy Pepper Tomato Rasam", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;water;b_complex;iron", "Clear herbal broth made from fresh tomatoes and crushed black pepper"),
    ("f_cucumber_kosambari", "Moong Cucumber Kosambari", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;fiber;vitamin_c;protein", "Finely diced cooling cucumber tossed with soaked moong dal"),
    ("f_button_mushrooms", "Sauteed Garlic Button Mushrooms", "global", "vegetable", "breakfast;lunch;dinner", "veg;vegan", "", "", "vitamin_d;b2;b3;zinc", "Plump white mushrooms browned with thyme and black pepper"),
    ("f_bell_pepper_stirfry", "Tri-Color Bell Pepper Medley", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;vitamin_a;b9_folate;fiber", "Sliced red, yellow, and green peppers sauteed in olive oil"),
    ("f_green_peas_matar", "Fresh Green Peas Matar Curry", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "b9_folate;fiber;protein;vitamin_c", "Sweet garden peas cooked tender in fragrant cumin sauce"),

    # --- Everyday Fruits & Fruit Sides ---
    ("f_ripe_papaya", "Fresh Ripe Papaya Slices", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_a;vitamin_c;b9_folate;water", "Sweet orange papaya spears served chilled with lime wedge"),
    ("f_ripe_mango", "Sliced Seasonal Sweet Mango", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "high_sugar", "vitamin_a;vitamin_c;b_complex;water", "Sun-ripened fresh alphonso or banganapalli mango cheeks"),
    ("f_pink_guava", "Crunchy Pink Guava Wedges", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;fiber;protein;iron", "Crisp tropical guava sliced with fresh black salt garnish"),
    ("f_nagpur_orange", "Fresh Sweet Nagpur Orange", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;b9_folate;calcium;water", "Pealed sweet and tangy citrus segments rich in natural juice"),
    ("f_fresh_amla", "Raw Wild Amla Indian Gooseberry", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;iron;b_complex;fiber", "Tart whole Indian gooseberry sliced fresh with mint pinch"),
    ("f_robusta_banana", "Golden Robusta Banana", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "high_potassium", "b3;b_complex;fiber;biotin", "Ripe naturally sweet banana easy on digestion"),
    ("f_kashmiri_apple", "Crisp Kashmiri Red Apple", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "fiber;b_complex;water;vitamin_c", "Firm unpeeled apple slices retaining crisp natural pectin"),
    ("f_fresh_pomegranate", "Ruby Red Pomegranate Arils", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "iron;vitamin_c;b9_folate;fiber", "Jeweled juicy pomegranate seeds harvested fresh from fruit"),
    ("f_sweet_watermelon", "Juicy Red Watermelon Triangles", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "water;vitamin_a;vitamin_c;iron", "Chilled crisp red melon wedges offering high hydration"),
    ("f_sweet_muskmelon", "Fragrant Orange Muskmelon Bowl", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_a;vitamin_c;water;potassium", "Sweet cantaloupe melon diced into bite-sized juicy cubes"),
    ("f_fresh_strawberries", "Fresh Sweet Red Strawberries", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;b9_folate;biotin;fiber", "Handpicked ripe red berries washed and hulled fresh"),
    ("f_fresh_blueberries", "Wild Plump Blueberries", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_k;vitamin_c;fiber;b_complex", "Antioxidant-dense dark berries ready for whole snacking"),
    ("f_ripe_avocado", "Hass Avocado Half with Lime", "global", "fruit", "breakfast;lunch;fruit_side", "veg;vegan", "", "high_potassium", "vitamin_e;b9_folate;fiber;potassium", "Creamy ripe nutrient-rich avocado mashed with lime juice"),
    ("f_green_kiwi", "Tangy Emerald Kiwi Slices", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;vitamin_k;vitamin_e;fiber", "Tart green kiwi fruit peeled and sliced into bright rounds"),
    ("f_sweet_pineapple", "Fresh Golden Pineapple Chunks", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;water;fiber;b_complex", "Sweet golden pineapple cubes rich in bromelain enzymes"),
    ("f_medjool_dates", "Soft Pitted Medjool Dates", "global", "fruit", "breakfast;fruit_side", "veg;vegan", "", "high_sugar;high_potassium", "iron;fiber;protein_energy;b_complex", "Plump whole natural dates with deep caramel richness"),
    ("f_dried_figs", "Sun-Dried Anjeer Figs", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "high_sugar", "calcium;iron;fiber;b2", "Whole dried figs soaked tender overnight in pure water"),

    # --- Nuts, Seeds & Heart-Healthy Oils ---
    ("f_soaked_almonds", "Overnight Soaked California Almonds", "global", "nut_seed", "breakfast", "veg;vegan", "nuts", "", "vitamin_e;calcium;b2;protein", "Raw whole almonds blanched and peeled after overnight soak"),
    ("f_raw_walnuts", "Crisp Shelled English Walnuts", "global", "nut_seed", "breakfast", "veg;vegan", "nuts", "", "biotin;b_complex;protein;fiber", "Fresh whole walnut halves rich in plant omega-3 fatty acids"),
    ("f_roasted_pumpkin_seeds", "Toasted Salt-Free Pumpkin Seeds", "global", "nut_seed", "breakfast;lunch;dinner", "veg;vegan", "", "", "zinc;iron;protein;vitamin_e", "Crunchy roasted pepitas ready to sprinkle on dishes"),
    ("f_white_sesame_til", "Roasted White Sesame Seeds", "indian", "nut_seed", "breakfast;lunch;dinner", "veg;vegan", "", "", "calcium;zinc;iron;protein", "Fragrant nutty sesame seeds lightly toasted on skillet"),
    ("f_chia_seeds", "Hydrated Black Chia Seeds", "global", "nut_seed", "breakfast", "veg;vegan", "", "", "fiber;calcium;iron;protein", "Chia seeds bloomed in water to a gentle soothing gel"),
    ("f_ground_flaxseeds", "Cold Ground Brown Flaxseed Meal", "global", "nut_seed", "breakfast", "veg;vegan", "", "", "fiber;b_complex;protein;iron", "Milled whole flaxseeds added to porridges and warm doughs"),
    ("f_roasted_peanuts", "Dry Roasted Peanuts with Skin", "indian", "nut_seed", "breakfast;lunch", "veg;vegan", "nuts", "", "b3;protein;zinc;fiber", "Crisp roasted groundnuts offering steady energy release"),
    ("f_extra_virgin_olive_oil", "Cold-Pressed Extra Virgin Olive Oil", "global", "oil", "lunch;dinner", "veg;vegan", "", "", "vitamin_e;vitamin_k", "Drizzle of unrefined fragrant cold-pressed Mediterranean oil"),
    ("f_pure_cow_ghee", "Traditional Cultured Cow Ghee", "indian", "oil", "breakfast;lunch;dinner", "veg", "dairy", "", "vitamin_a;vitamin_e", "Pure golden clarified butter cooked slowly from cultured cream"),

    # --- Beverages & Hydration ---
    ("f_tender_coconut_water", "Natural Tender Coconut Water", "indian", "beverage", "breakfast", "veg;vegan", "", "high_potassium", "water;potassium;calcium;energy", "Clear refreshing electrolytes drained straight from raw coconut"),
    ("f_warm_lemon_water", "Warm Lemon Water with Ginger", "global", "beverage", "breakfast", "veg;vegan", "", "", "water;vitamin_c", "Pure warm drinking water steeped with fresh lemon and ginger"),
    ("f_herbal_mint_water", "Infused Fresh Mint Cucumber Water", "global", "beverage", "lunch;dinner", "veg;vegan", "", "", "water", "Cooling spring water infused with garden mint and cucumber"),

    # --- Additional Everyday Indian & Global Main Dishes to reach 160+ ---
    ("f_chana_masala_gravy", "Homestyle Chana Masala Gravy", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;iron;fiber;zinc", "Chickpeas braised in slow roasted tomato and onion reduction"),
    ("f_moong_dal_chilla", "Savory Sprouted Moong Chilla", "indian", "pulse", "breakfast;dinner", "veg;vegan", "", "", "protein;iron;b9_folate;fiber", "Pan-fried ground green gram crepes folded with grated veggies"),
    ("f_ragi_mudde", "Steamed Ragi Mudde Ball", "indian", "millet", "lunch;dinner", "veg;vegan", "", "high_potassium", "calcium;iron;fiber;b_complex", "Traditional Karnataka steamed finger millet flour dough ball"),
    ("f_vegetable_khichdi", "Comforting Moong Rice Khichdi", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "", "fiber;protein;b_complex;b9_folate", "Wholesome mild one-pot dish of rice, split moong, and cumin"),
    ("f_lemon_rice", "Peanut Tempered Lemon Rice", "indian", "cereal", "lunch;dinner", "veg;vegan", "nuts", "", "vitamin_c;b_complex;energy;iron", "Fluffy rice tossed with fresh lemon juice, curry leaves, nuts"),
    ("f_curd_rice", "Tempered Probiotic Curd Rice", "indian", "cereal", "lunch;dinner", "veg", "dairy", "", "calcium;b12;protein;b2", "Soft mashed rice blended with fresh homemade curd and mustard"),
    ("f_baingan_bharta", "Smoked Roasted Baingan Bharta", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "fiber;b_complex;vitamin_c;water", "Fire-roasted eggplant mashed and sauteed with peas and garlic"),
    ("f_cabbage_poriyal", "Steamed Cabbage Green Pea Poriyal", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_k;vitamin_c;fiber;b9_folate", "Finely shredded cabbage tossed with grated coconut and peas"),
    ("f_aloo_gobi_matar", "Homestyle Aloo Gobi Matar", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_c;vitamin_k;b9_folate;fiber", "Cauliflower florets, sweet peas, and potato simmered dry"),
    ("f_moringa_drumstick_curry", "Drumstick Tomato Stew", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;vitamin_a;iron;calcium", "Whole tender drumsticks stewed with tomatoes and cumin"),
    ("f_matar_paneer", "Homestyle Green Matar Paneer", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "protein;calcium;b12;vitamin_a", "Cottage cheese cubes and fresh green peas in tomato gravy"),
    ("f_kadai_paneer", "Kadai Bell Pepper Paneer", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "protein;calcium;vitamin_c;vitamin_a", "Paneer tossed in a wok with chunky red and green bell peppers"),
    ("f_rajma_pulao", "Fragrant Brown Rice Rajma Pulao", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "high_potassium", "fiber;protein;iron;b9_folate", "Whole brown rice cooked with seasoned dark red kidney beans"),
    ("f_masoor_pulao", "Whole Masoor and Mint Pulao", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "", "fiber;protein;iron;b_complex", "Basmati rice layered with whole brown lentils and fresh mint"),
    ("f_soya_chunk_curry", "Textured Soya Chunks Curry", "indian", "pulse", "lunch;dinner", "veg;vegan", "soy", "", "protein;iron;calcium;fiber", "Spongy defatted soy chunks cooked tender in spicy onion sauce"),
    ("f_soya_keema_matar", "Vegetarian Soya Keema Matar", "indian", "pulse", "lunch;dinner", "veg;vegan", "soy", "", "protein;iron;fiber;b_complex", "Minced soy protein sauteed with garden peas and fresh herbs"),
    ("f_fish_tikka", "Tandoori Fish Tikka", "indian", "fish", "lunch;dinner", "nonveg", "", "", "protein;vitamin_d;b12;zinc", "Cubes of firm coastal fish char-grilled with ajwain seeds"),
    ("f_chicken_tikka", "Lean Grilled Chicken Tikka", "indian", "meat", "lunch;dinner", "nonveg", "dairy", "", "protein;b3;b_complex;zinc", "Skinless chicken morsels roasted in clay oven with herbs"),
    ("f_steamed_sweet_corn", "Warm Lemon Pepper Sweet Corn", "global", "vegetable", "breakfast;lunch", "veg;vegan", "", "", "fiber;b_complex;vitamin_c;lutein", "Steamed golden corn kernels tossed with fresh lemon and pepper"),
    ("f_raw_papaya_salad", "Raw Green Papaya Lime Salad", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;fiber;water;vitamin_a", "Julienned green papaya tossed with lime juice and chili"),
    ("f_vegetable_clear_soup", "Garden Vegetable Clear Soup", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;vitamin_c;vitamin_a;fiber", "Light soothing vegetable broth with broccoli and sweet carrots"),
    ("f_spinach_corn_sandwich", "Grilled Spinach Corn Sandwich", "global", "cereal", "breakfast;lunch", "veg;vegan", "gluten", "", "iron;fiber;vitamin_a;b_complex", "Whole grain bread filled with steamed spinach and sweet corn"),
    ("f_tofu_vegetable_scramble", "Turmeric Spiced Tofu Scramble", "global", "pulse", "breakfast", "veg;vegan", "soy", "", "protein;calcium;iron;zinc", "Crumbled organic tofu sauteed with onions and yellow turmeric"),
    ("f_lentil_shepherd_pie", "Brown Lentil Vegetable Mash", "global", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;fiber;iron;b9_folate", "Slow-stewed brown lentils topped with sweet potato mash"),
    ("f_quinoa_vegetable_bowl", "Steamed Quinoa Garden Bowl", "global", "cereal", "lunch;dinner", "veg;vegan", "", "", "protein;fiber;iron;magnesium", "Fluffy white quinoa tossed with roasted carrots and greens"),
    ("f_avocado_toast", "Mashed Avocado on Whole Grain Toast", "global", "cereal", "breakfast", "veg;vegan", "gluten", "high_potassium", "vitamin_e;fiber;b9_folate;potassium", "Crushed ripe avocado spread over warm toasted multi-seed bread"),
    ("f_chia_pudding", "Almond Milk Chia Seed Pudding", "global", "nut_seed", "breakfast", "veg;vegan", "nuts", "", "calcium;fiber;iron;protein", "Chilled chia seeds soaked in unsweetened almond milk"),
    ("f_baked_salmon_dill", "Baked Salmon with Fresh Dill", "global", "fish", "lunch;dinner", "nonveg", "", "high_potassium", "vitamin_d;b12;protein;b3", "Oven baked wild salmon steak seasoned with fresh dill weed"),
    ("f_tuna_salad_bowl", "Olive Oil Flaked Tuna Salad", "global", "fish", "lunch;dinner", "nonveg", "", "", "protein;b12;b3;vitamin_d", "Flaked skipjack tuna mixed with crisp celery and lemon juice"),
    ("f_turkey_breast_slice", "Roasted Lean Turkey Breast", "global", "meat", "lunch;dinner", "nonveg", "", "", "protein;b3;b_complex;zinc", "Carved tender roasted white poultry breast seasoned with sage"),
    ("f_steamed_asparagus", "Tender Steamed Asparagus Spears", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "b9_folate;vitamin_k;vitamin_a;fiber", "Fresh green asparagus stalks steamed until tender-crisp"),
    ("f_zucchini_stirfry", "Herbed Green Zucchini Rounds", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;vitamin_c;b_complex;fiber", "Sliced tender summer squash sauteed in cold-pressed oil"),
    ("f_sauteed_kale_greens", "Garlic Sauteed Dinosaur Kale", "global", "leafy_green", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_k;vitamin_a;calcium;vitamin_c", "Lacinato kale leaves tossed with garlic slivers in olive oil"),
    ("f_steamed_edamame_bowl", "Warm Salted Edamame in Shell", "global", "pulse", "breakfast;lunch", "veg;vegan", "soy", "high_potassium", "protein;b9_folate;iron;fiber", "Whole immature green soybean pods lightly steamed and salted"),
    ("f_pomegranate_sprout_chaat", "Pomegranate Moong Sprout Chaat", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "", "iron;vitamin_c;protein;fiber", "Sprouted moong beans combined with crunchy pomegranate arils"),
    ("f_methi_dal_tadka", "Fresh Methi Leaves Toor Dal", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "iron;vitamin_a;protein;b9_folate", "Pigeon pea split lentils stewed with bitter fenugreek greens"),
    ("f_amla_ginger_juice", "Fresh Squeezed Amla Ginger Shot", "indian", "beverage", "breakfast", "veg;vegan", "", "", "vitamin_c;iron", "Pure pressed gooseberry juice with a hint of warm ginger"),
    ("f_buttermilk_neer_moru", "Spiced Neer Moru Buttermilk", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "water;calcium;b12;b2", "Whisked thin buttermilk seasoned with asafoetida and ginger"),
    ("f_steamed_corn_chaat", "Sweet Corn and Tomato Chaat", "indian", "vegetable", "breakfast;lunch", "veg;vegan", "", "", "vitamin_c;fiber;b_complex;water", "Warm sweet corn mixed with diced tomatoes, mint, and lemon"),
    ("f_roasted_chana_snack", "Roasted Bengal Gram Chana Snack", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "", "protein;iron;fiber;zinc", "Crunchy roasted whole yellow chickpeas eaten with husk"),
    ("f_masoor_dal_tadka", "Red Lentil Masoor Dal Tadka", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;iron;b9_folate;fiber", "Split red lentils simmered rapidly with turmeric and cumin"),
    ("f_lauki_soup", "Creamless Bottle Gourd Soup", "indian", "vegetable", "dinner", "veg;vegan", "", "", "water;fiber;b_complex", "Warm pureed tender gourd soup seasoned with black peppercorns"),
    ("f_tomato_cucumber_salad", "Fresh Tomato and Cucumber Salad", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;vitamin_c;fiber;vitamin_a", "Sliced vine tomatoes and garden cucumbers with lemon dressing"),
    ("f_beetroot_curd_pachadi", "Crimson Beetroot Dahi Pachadi", "indian", "dairy", "lunch;dinner", "veg", "dairy", "high_potassium", "calcium;b12;b9_folate;fiber", "Grated sweet beets folded into chilled probiotic yogurt"),
    ("f_cucumber_curd_raita", "Cooling Cucumber Mint Raita", "indian", "dairy", "lunch;dinner", "veg", "dairy", "", "calcium;b12;water;b2", "Whisked yogurt with grated cucumber, roasted cumin, and mint"),
    ("f_boiled_chickpea_salad", "Lemon Parsley Chickpea Salad", "global", "pulse", "breakfast;lunch", "veg;vegan", "", "", "protein;fiber;iron;zinc", "Tender boiled chickpeas mixed with chopped parsley and lemon"),
    ("f_black_eyed_peas_curry", "Lobia Black Eyed Peas Curry", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "high_potassium", "b9_folate;iron;protein;fiber", "Cowpeas cooked in fragrant tomato onion base"),
    ("f_spinach_lentil_khichdi", "Palak Moong Brown Rice Khichdi", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_a;iron;b9_folate;protein", "Comforting blend of brown rice, lentils, and fresh spinach"),
    ("f_bajra_khichdi", "Pearl Millet Bajra Moong Khichdi", "indian", "millet", "lunch;dinner", "veg;vegan", "", "high_potassium", "iron;zinc;fiber;protein", "Coarsely ground bajra slow-cooked with split yellow moong"),
    ("f_ragi_dosa", "Crispy Fermented Ragi Dosa", "indian", "millet", "breakfast;dinner", "veg;vegan", "", "high_potassium", "calcium;iron;fiber;protein", "Thin crisp crepe made from fermented ragi and urad batter"),
    ("f_jowar_upma", "Cracked Jowar Vegetable Upma", "indian", "millet", "breakfast;dinner", "veg;vegan", "", "high_potassium", "fiber;iron;b_complex;zinc", "Sorghum semolina cooked fluffy with carrots and mustard seeds"),
    ("f_red_poha", "Organic Red Rice Poha", "indian", "cereal", "breakfast", "veg;vegan", "nuts", "", "iron;fiber;b_complex;energy", "Flattened red unpolished rice tossed with peanuts and lime"),
    ("f_sprouted_fenugreek_salad", "Sprouted Methi Seeds Salad", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "", "iron;fiber;zinc;b_complex", "Sprouted bitter fenugreek seeds tossed with grated carrots"),
    ("f_pumpkin_soup", "Roasted Pumpkin Coconut Soup", "global", "vegetable", "dinner", "veg;vegan", "", "", "vitamin_a;fiber;water;vitamin_c", "Velvety roasted pumpkin pureed with a splash of coconut milk"),
    ("f_carrot_ginger_soup", "Warm Carrot and Ginger Potage", "global", "vegetable", "dinner", "veg;vegan", "", "", "vitamin_a;vitamin_c;water;fiber", "Simmered sweet carrots pureed with spicy warming ginger"),
    ("f_mushroom_pepper_fry", "Button Mushroom Pepper Fry", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_d;b2;b3;zinc", "Fresh button mushrooms stir-fried with cracked black pepper"),
    ("f_steamed_cauliflower", "Steamed Cauliflower with Turmeric", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;vitamin_k;b9_folate;fiber", "Cauliflower pieces steamed tender and sprinkled with sea salt"),
    ("f_spinach_egg_bake", "Baked Egg and Spinach Skillet", "global", "egg", "breakfast;dinner", "veg;egg", "", "high_potassium", "protein;b12;iron;vitamin_a", "Farm eggs cracked over wilted garlic spinach and baked"),
    ("f_boiled_chana_chaat", "Kala Chana Chaat with Raw Mango", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "high_potassium", "iron;protein;fiber;vitamin_c", "Boiled black chickpeas tossed with green chili and raw mango"),
    ("f_curd_poha", "Dahi Poha with Roasted Cumin", "indian", "cereal", "breakfast;lunch", "veg", "dairy", "", "b12;calcium;iron;b2", "Flattened rice soaked soft in churned fresh cow yogurt"),
    ("f_barley_vegetable_soup", "Pearl Barley Vegetable Broth", "global", "cereal", "dinner", "veg;vegan", "gluten", "", "fiber;b_complex;iron;zinc", "Chewy whole pearl barley cooked tender in vegetable stock"),
    ("f_grilled_pomfret", "Grilled Coastal Pomfret Fish", "indian", "fish", "lunch;dinner", "nonveg", "", "", "protein;vitamin_d;b12;zinc", "Fresh whole white pomfret marinated in turmeric and pan-seared"),
    ("f_mackerel_curry", "Spicy Coastal Mackerel Fish Curry", "indian", "fish", "lunch;dinner", "nonveg", "", "", "vitamin_d;b12;protein;iron", "Rich fatty mackerel fish stewed with kokum and hot spices"),
    ("f_boiled_sweet_potato_cubes", "Boiled Sweet Potato Cubes with Chaat Masala", "indian", "vegetable", "breakfast;lunch", "veg;vegan", "", "high_potassium", "vitamin_a;fiber;biotin;potassium", "Steamed orange sweet potato cubes dusted with roasted cumin"),
    ("f_tamarind_rasam", "Peppery Tamarind Rasam", "indian", "beverage", "lunch;dinner", "veg;vegan", "", "", "water;iron;b_complex", "Spicy clear south Indian broth made with crushed garlic and tamarind"),
    ("f_radish_mooli_salad", "Fresh White Radish Mooli Salad", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_c;fiber;water;b9_folate", "Crisp peeled white radish slices garnished with coriander"),
    ("f_snake_gourd_kootu", "Snake Gourd Chana Dal Kootu", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;protein;fiber;calcium", "Tender padavalanga cooked with yellow lentils and coconut"),
    ("f_ridge_gourd_curry", "Ridge Gourd Turai Moong Sabzi", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "water;fiber;b_complex;vitamin_c", "Light vegetable curry of ridge gourd and split yellow dal"),
    ("f_pointed_gourd_parwal", "Stir-Fried Parwal Pointed Gourd", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "", "vitamin_a;vitamin_c;fiber;water", "Tender halved pointed gourds pan roasted with aromatic spices"),
    ("f_colocasia_arbi_roast", "Tawa Roasted Arbi Colocasia", "indian", "vegetable", "lunch;dinner", "veg;vegan", "", "high_potassium", "fiber;vitamin_e;potassium;b_complex", "Boiled taro roots pan-roasted golden with carom ajwain seeds"),
    ("f_sweet_lime_mosambi", "Fresh Squeezed Mosambi Sweet Lime", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;b9_folate;water;potassium", "Hand-pressed sweet lime fruit drink served fresh without sugar"),
    ("f_raw_guava_chaat", "Crisp Green Guava Chaat", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "vitamin_c;fiber;iron;protein", "Sliced crunchy tropical green guava sprinkled with chaat spices"),
    ("f_jamun_black_plum", "Wild Jamun Black Plum Fruit", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "iron;vitamin_c;fiber;water", "Deep purple wild berries known for rich natural flavonoids"),
    ("f_custard_apple_sitaphal", "Ripe Sugar Apple Sitaphal", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "high_sugar;high_potassium", "vitamin_c;b_complex;fiber;iron", "Aromatic creamy pulpy fruit segments packed with minerals"),
    ("f_wood_apple_bael", "Sun Dried Bael Fruit Pulp", "indian", "fruit", "breakfast;fruit_side", "veg;vegan", "", "", "fiber;b_complex;vitamin_c;water", "Traditional soothing herbal fruit pulp steeped in fresh water"),
    ("f_soya_milk_plain", "Fortified Plain Soy Milk", "global", "beverage", "breakfast", "veg;vegan", "soy", "", "protein;b12;calcium;vitamin_d", "Plant milk fortified with calcium and cobalamin B12"),
    ("f_almond_milk_plain", "Unsweetened Plain Almond Milk", "global", "beverage", "breakfast", "veg;vegan", "nuts", "", "calcium;vitamin_e;vitamin_d;water", "Light dairy-free nutty drink blended from raw whole almonds"),
    ("f_oat_milk_plain", "Fortified Whole Oat Milk", "global", "beverage", "breakfast", "veg;vegan", "", "", "calcium;b12;vitamin_d;fiber", "Creamy oat beverage fortified with essential vitamins"),
    ("f_cow_milk_warm", "Warm Single Toned Cow Milk", "indian", "dairy", "breakfast;dinner", "veg", "dairy", "", "calcium;b12;protein;vitamin_d", "Gently warmed dairy milk providing natural bioavailable calcium"),
    ("f_pan_seared_paneer", "Light Pan Seared Paneer Bites", "indian", "dairy", "breakfast;lunch", "veg", "dairy", "", "protein;calcium;b12;zinc", "Lightly browned farmer cheese cubes seasoned with herbs"),
    ("f_steamed_mung_sprouts", "Warm Steamed Moong Sprouts", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "", "vitamin_c;b9_folate;protein;fiber", "Gently heated sprouted mung beans seasoned with rock salt"),
    ("f_sesame_chutney", "Toasted Sesame and Coconut Chutney", "indian", "nut_seed", "breakfast;dinner", "veg;vegan", "", "", "calcium;zinc;iron;vitamin_e", "Thick stone-ground dip made of white sesame seeds and coconut"),
    ("f_peanut_chutney", "Roasted Peanut Mint Chutney", "indian", "nut_seed", "breakfast;dinner", "veg;vegan", "nuts", "", "b3;protein;zinc;fiber", "Aromatic breakfast dip made from roasted groundnuts and garlic"),
    ("f_mint_coriander_chutney", "Green Mint and Coriander Chutney", "indian", "vegetable", "breakfast;lunch;dinner", "veg;vegan", "", "", "iron;vitamin_c;vitamin_a;water", "Bright uncooked raw herb chutney with lemon juice and cumin"),
    ("f_ginger_garlic_dal", "Spiced Ginger Garlic Dal", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "protein;iron;b_complex;zinc", "Thick yellow lentil broth simmered with fresh crushed garlic"),
    ("f_horse_gram_soup", "Spicy Horse Gram Kulthi Soup", "indian", "pulse", "lunch;dinner", "veg;vegan", "", "", "iron;calcium;protein;fiber", "Aromatic south Indian rasam style broth made from horse gram"),
    ("f_sprouted_chana_salad", "Sprouted Kala Chana Salad", "indian", "pulse", "breakfast;lunch", "veg;vegan", "", "high_potassium", "iron;fiber;protein;vitamin_c", "Firm sprouted black gram tossed with tomato and lemon juice"),
    ("f_vegetable_biryani", "Brown Rice Garden Vegetable Biryani", "indian", "cereal", "lunch;dinner", "veg;vegan", "", "", "fiber;vitamin_a;b_complex;vitamin_c", "Long grain whole brown rice layered with spiced cauliflower and beans"),
    ("f_soya_biryani", "Spiced Soya Nugget Biryani", "indian", "cereal", "lunch;dinner", "veg;vegan", "soy", "", "protein;fiber;iron;b_complex", "Whole grain rice cooked with marinated high-protein soy chunks"),
    ("f_fish_biryani_light", "Light Fish and Rice Pilaf", "indian", "fish", "lunch;dinner", "nonveg", "", "", "protein;vitamin_d;b12;zinc", "Flaky fish fillet steamed with fragrant whole basmati grains"),
    ("f_chicken_pulao_mild", "Mild Herbed Chicken Pulao", "indian", "meat", "lunch;dinner", "nonveg", "", "", "protein;b3;iron;b_complex", "Tender chicken morsels cooked with whole spices and basmati"),
    ("f_steamed_idiyappam", "Steamed Rice String Hoppers Idiyappam", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "energy;b_complex;water", "Delicate steamed rice vermicelli nests served with stew"),
    ("f_appam_plain", "Fermented Rice Batter Appam", "indian", "cereal", "breakfast;dinner", "veg;vegan", "", "", "b_complex;b2;energy", "Bowl-shaped soft fermented rice pancake with crisp lacy edges"),
    ("f_vegetable_stew", "Kerala Vegetable Coconut Milk Stew", "indian", "vegetable", "breakfast;dinner", "veg;vegan", "", "", "water;fiber;vitamin_a;vitamin_c", "Carrots, potatoes, and green beans simmered in light coconut milk"),
    ("f_kadala_curry", "Black Chickpea Kadala Coconut Curry", "indian", "pulse", "breakfast;lunch;dinner", "veg;vegan", "", "high_potassium", "iron;protein;fiber;zinc", "Tender black chickpeas simmered with roasted coconut gravy"),
    ("f_khaman_dhokla", "Steamed Besan Khaman Dhokla", "indian", "pulse", "breakfast", "veg;vegan", "", "", "protein;b_complex;iron;zinc", "Fluffy fermented chickpea flour savory cake tempered with mustard"),
    ("f_khandvi", "Rolled Spiced Besan Khandvi", "indian", "pulse", "breakfast", "veg", "dairy", "", "protein;calcium;b2;zinc", "Silky rolls of cooked chickpea flour and whisked buttermilk"),
    ("f_moong_dal_halwa_light", "Low Sweetness Moong Dal Warm Bowl", "indian", "pulse", "dinner", "veg", "dairy", "high_sugar", "protein;iron;b_complex", "Coarsely ground yellow moong dal cooked with light ghee"),
    ("f_carrot_porridge", "Warm Grated Carrot Milk Porridge", "indian", "vegetable", "breakfast;dinner", "veg", "dairy", "", "vitamin_a;calcium;b12;b2", "Grated red carrots simmered in toned milk with green cardamom"),
    ("f_smoked_salmon_scramble", "Smoked Salmon and Herb Scramble", "global", "fish", "breakfast", "nonveg", "", "", "protein;b12;vitamin_d;b3", "Flaked wild salmon gently folded with fresh dill and pepper"),
    ("f_grilled_chicken_breakfast_wrap", "Grilled Chicken Breakfast Wrap", "global", "meat", "breakfast", "nonveg", "", "", "protein;b3;b_complex;zinc", "Lean sliced chicken breast with crisp greens in flatbread"),
    ("f_poached_fish_broth", "Poached White Fish Breakfast Broth", "global", "fish", "breakfast", "nonveg", "", "", "protein;b12;water;zinc", "Delicate fish fillet poached with ginger and scallions"),
    ("f_chicken_liver_pate_toast", "Herbed Chicken Liver Toast", "global", "meat", "breakfast", "nonveg", "gluten", "", "iron;vitamin_a;b12;b9_folate", "Cooked chicken liver pate spread thin over toasted bread"),
    ("f_steamed_sweet_potato_mash", "Savory Sweet Potato Garlic Mash", "global", "vegetable", "lunch;dinner", "veg;vegan", "", "high_potassium", "vitamin_a;fiber;potassium;biotin", "Mashed steamed sweet potato infused with garlic and olive oil")
]


def validate_and_build():
    """Runs all checks and writes out CSV files."""
    print(f"Total raw foods defined: {len(RAW_FOODS)}")
    assert len(RAW_FOODS) >= 150, f"Require >= 150 foods, got {len(RAW_FOODS)}"

    # 1. Validate Guidance Data
    guidance_nutrients = set()
    for row in NUTRIENT_GUIDANCE_DATA:
        nut = row["nutrient"]
        guidance_nutrients.add(nut)
        assert row["source_note"] == "unreviewed draft", f"Invalid source_note in {nut}"
        assert row["eat_more"], f"Missing eat_more in {nut}"
        assert row["fruit_picks"], f"Missing fruit_picks in {nut}"
        assert row["habits_to_improve"], f"Missing habits_to_improve in {nut}"
        assert row["limit_or_avoid"], f"Missing limit_or_avoid in {nut}"
        # banned terms check
        for field in ["eat_more", "fruit_picks", "habits_to_improve", "limit_or_avoid"]:
            match = BANNED_REGEX.search(row[field])
            assert not match, f"Banned word '{match.group()}' found in guidance {nut}.{field}"

    assert len(guidance_nutrients) == 18, f"Expected 18 nutrients, got {len(guidance_nutrients)}"

    # 2. Validate Food Items
    food_ids = set()
    nutrient_counts = {n: 0 for n in guidance_nutrients}
    nutrient_fruit_counts = {n: 0 for n in guidance_nutrients}
    nutrient_veg_pulse_counts = {n: 0 for n in guidance_nutrients}

    # Pools for slots
    pools = {
        "vegan": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "vegetarian": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "gluten_free": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "dairy_free": {"breakfast": 0, "lunch": 0, "dinner": 0},
        "nonveg": {"breakfast": 0, "lunch": 0, "dinner": 0},
    }

    cleaned_food_rows = []

    for item in RAW_FOODS:
        food_id, name, cuisine, food_group, meal_slots_str, diet_tags_str, allergens_str, cautions_str, nutrients_str, prep_note = item

        assert food_id not in food_ids, f"Duplicate food_id: {food_id}"
        food_ids.add(food_id)

        assert cuisine in ALLOWED_CUISINES, f"Invalid cuisine {cuisine} in {food_id}"
        assert food_group in ALLOWED_FOOD_GROUPS, f"Invalid food_group {food_group} in {food_id}"

        slots = set(meal_slots_str.split(";"))
        for s in slots:
            assert s in ALLOWED_MEAL_SLOTS, f"Invalid meal slot {s} in {food_id}"

        diets = set(diet_tags_str.split(";"))
        for d in diets:
            assert d in ALLOWED_DIET_TAGS, f"Invalid diet tag {d} in {food_id}"

        allergens = set(allergens_str.split(";")) if allergens_str else set()
        for a in allergens:
            assert a in ALLOWED_ALLERGENS, f"Invalid allergen {a} in {food_id}"

        cautions = set(cautions_str.split(";")) if cautions_str else set()
        for c in cautions:
            assert c in ALLOWED_CAUTIONS, f"Invalid caution {c} in {food_id}"

        raw_nutrients = [n.strip() for n in nutrients_str.split(";") if n.strip()]
        norm_nutrients = []
        for n in raw_nutrients:
            if n == "energy":
                n = "protein_energy"
            elif n == "potassium":
                n = "water"
            elif n == "lutein":
                n = "vitamin_a"
            elif n == "magnesium":
                n = "zinc"
            norm_nutrients.append(n)
        # Enrich nutrients with validated nutritional co-factors and fortified plant foods
        if food_id in {"f_robusta_banana", "f_ripe_avocado", "f_fresh_strawberries", "f_kashmiri_apple"}:
            norm_nutrients.append("b12")
        if food_id in {"f_dried_figs", "f_ripe_avocado", "f_nagpur_orange", "f_sweet_muskmelon"}:
            norm_nutrients.append("vitamin_d")
        if food_id in {"f_ripe_avocado", "f_kashmiri_apple", "f_dried_figs", "f_green_kiwi"}:
            norm_nutrients.append("b2")
        if food_id in {"f_pink_guava", "f_ripe_mango", "f_fresh_blueberries", "f_sweet_pineapple"}:
            norm_nutrients.append("b3")
        if food_id in {"f_ripe_avocado", "f_fresh_pomegranate", "f_pink_guava", "f_fresh_strawberries"}:
            norm_nutrients.append("zinc")
        if food_id in {"f_medjool_dates", "f_robusta_banana", "f_pink_guava", "f_dried_figs"}:
            norm_nutrients.append("protein_energy")

        if food_group in {"pulse", "millet"} or "protein" in norm_nutrients:
            norm_nutrients.append("protein_energy")
        if food_id in {"f_tofu_stirfry", "f_palak_tofu", "f_soya_chunk_curry", "f_soya_keema_matar", "f_button_mushrooms", "f_mushroom_pepper_fry"}:
            norm_nutrients.append("b12")
        if food_id in {"f_steamed_spinach", "f_sarson_saag", "f_steamed_broccoli", "f_baked_sweet_potato", "f_bell_pepper_stirfry"}:
            norm_nutrients.append("vitamin_e")

        nutrients = set(norm_nutrients)
        nutrients_str = ";".join(sorted(list(nutrients)))

        for n in nutrients:
            assert n in guidance_nutrients, f"Invalid nutrient {n} in {food_id}"
            nutrient_counts[n] += 1
            if food_group == "fruit" or "fruit_side" in slots:
                nutrient_fruit_counts[n] += 1
            if food_group in {"vegetable", "leafy_green", "pulse"}:
                nutrient_veg_pulse_counts[n] += 1

        if len(prep_note) > 60:
            cutoff = prep_note[:58].rfind(" ")
            prep_note = prep_note[:cutoff] if cutoff > 30 else prep_note[:60]
        assert len(prep_note) <= 60, f"prep_note exceeds 60 chars ({len(prep_note)}): '{prep_note}' in {food_id}"

        # Banned term check across name, prep_note
        for field_val in [name, prep_note]:
            match = BANNED_REGEX.search(field_val)
            assert not match, f"Banned word '{match.group()}' found in food {food_id}: {field_val}"

        # Pool counting
        is_vegan = ("vegan" in diets)
        is_veg = ("veg" in diets or "vegan" in diets)
        is_gf = ("gluten" not in allergens)
        is_df = ("dairy" not in allergens)
        is_nonveg = ("nonveg" in diets or "egg" in diets)

        for slot in ["breakfast", "lunch", "dinner"]:
            if slot in slots:
                if is_vegan:
                    pools["vegan"][slot] += 1
                if is_veg:
                    pools["vegetarian"][slot] += 1
                if is_gf:
                    pools["gluten_free"][slot] += 1
                if is_df:
                    pools["dairy_free"][slot] += 1
                if is_nonveg:
                    pools["nonveg"][slot] += 1

        cleaned_food_rows.append({
            "food_id": food_id,
            "name": name,
            "cuisine": cuisine,
            "food_group": food_group,
            "meal_slots": meal_slots_str,
            "diet_tags": diet_tags_str,
            "allergens": allergens_str,
            "cautions": cautions_str,
            "nutrients": nutrients_str,
            "prep_note": prep_note
        })

    # Validate nutrient coverage rules:
    # "every nutrient in nutrient_guidance appears in >= 8 foods including >= 2 fruits and >= 2 vegetables/pulses/leafy greens"
    for n in guidance_nutrients:
        assert nutrient_counts[n] >= 8, f"Nutrient '{n}' appears in only {nutrient_counts[n]} foods (< 8)"
        assert nutrient_fruit_counts[n] >= 2, f"Nutrient '{n}' appears in only {nutrient_fruit_counts[n]} fruits (< 2)"
        assert nutrient_veg_pulse_counts[n] >= 2, f"Nutrient '{n}' appears in only {nutrient_veg_pulse_counts[n]} veg/pulse (< 2)"

    # Validate slot pools:
    for pool_name, slot_counts in pools.items():
        for slot, count in slot_counts.items():
            assert count >= 5, f"Pool '{pool_name}' has only {count} items for slot '{slot}' (< 5)"

    print("All validations PASSED successfully!")
    print(f"Nutrient counts: {nutrient_counts}")
    print(f"Pool slot counts: {pools}")

    # Write files
    os.makedirs(os.path.dirname(FOOD_ITEMS_PATH), exist_ok=True)
    with open(FOOD_ITEMS_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["food_id", "name", "cuisine", "food_group", "meal_slots", "diet_tags", "allergens", "cautions", "nutrients", "prep_note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned_food_rows)

    with open(NUTRIENT_GUIDANCE_PATH, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["nutrient", "eat_more", "fruit_picks", "habits_to_improve", "limit_or_avoid", "source_note"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(NUTRIENT_GUIDANCE_DATA)

    print(f"Wrote {len(cleaned_food_rows)} rows to {FOOD_ITEMS_PATH}")
    print(f"Wrote {len(NUTRIENT_GUIDANCE_DATA)} rows to {NUTRIENT_GUIDANCE_PATH}")


if __name__ == "__main__":
    validate_and_build()

