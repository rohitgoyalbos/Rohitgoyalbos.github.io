"""
Synthetic data generator for LLM Content Quality Evaluator.
Generates realistic product data, content variations, and performance metrics.
"""

import random
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from faker import Faker

fake = Faker()

# ============== Product Templates by Category ==============

ELECTRONICS_TEMPLATES = {
    "Smartphones": {
        "brands": ["TechBrand", "PhonePro", "SmartCore", "MobileMax", "NexGen"],
        "name_patterns": ["{brand} Pro Max {version}", "{brand} Ultra {version}", "{brand} {version} Plus"],
        "features": [
            "Super Retina XDR display", "A17 Pro chip", "48MP main camera",
            "USB-C connectivity", "5G capable", "Face ID", "Ceramic Shield",
            "MagSafe compatible", "ProMotion technology", "Cinematic mode"
        ],
        "materials": ["Aluminum", "Ceramic Shield glass", "Titanium", "Stainless Steel"],
        "specs_ranges": {
            "display_size": (5.8, 6.9),
            "weight": (150, 240),
            "battery": (3500, 5000),
            "price": (699, 1499)
        }
    },
    "Laptops": {
        "brands": ["TechBook", "CompuPro", "WorkStation", "CloudBook", "ProBook"],
        "name_patterns": ["{brand} Pro {version}", "{brand} Air {version}", "{brand} Ultra {version}"],
        "features": [
            "Retina display", "M3 chip", "16GB unified memory",
            "512GB SSD", "Magic Keyboard", "Touch Bar", "Face ID",
            "Thunderbolt 4", "Wi-Fi 6E", "All-day battery"
        ],
        "materials": ["Aluminum", "Recycled Aluminum", "Magnesium alloy"],
        "specs_ranges": {
            "display_size": (13.3, 16.2),
            "weight": (1200, 2200),
            "battery_hours": (10, 22),
            "price": (999, 3499)
        }
    },
    "Headphones": {
        "brands": ["AudioMax", "SoundPro", "BeatWave", "HearClear", "SonicPure"],
        "name_patterns": ["{brand} Pro {version}", "{brand} Studio {version}", "{brand} Air {version}"],
        "features": [
            "Active Noise Cancellation", "Spatial Audio", "Transparency mode",
            "30-hour battery life", "Bluetooth 5.3", "Premium drivers",
            "Adaptive EQ", "Touch controls", "Voice assistant support"
        ],
        "materials": ["Anodized aluminum", "Memory foam", "Premium leather", "Stainless steel"],
        "specs_ranges": {
            "battery_hours": (20, 40),
            "weight": (180, 380),
            "driver_size": (30, 50),
            "price": (149, 549)
        }
    }
}

FASHION_TEMPLATES = {
    "Clothing": {
        "brands": ["StyleCraft", "UrbanWear", "EcoThreads", "LuxFashion", "ModernFit"],
        "name_patterns": ["{brand} {adjective} {item}", "{adjective} {item} by {brand}"],
        "adjectives": ["Premium", "Classic", "Modern", "Essential", "Signature"],
        "items": ["T-Shirt", "Polo Shirt", "Dress Shirt", "Jacket", "Sweater"],
        "features": [
            "100% organic cotton", "Moisture-wicking fabric", "Wrinkle-resistant",
            "Machine washable", "Sustainable materials", "Perfect fit technology"
        ],
        "materials": ["Cotton", "Organic Cotton", "Linen", "Wool", "Cashmere", "Polyester blend"],
        "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
        "colors": ["Navy Blue", "White", "Black", "Gray", "Olive", "Burgundy"],
        "specs_ranges": {"price": (29, 299)}
    },
    "Shoes": {
        "brands": ["StepPro", "ComfortWalk", "UrbanStep", "AthleteFoot", "ClassicSole"],
        "name_patterns": ["{brand} {style} {version}", "{style} {version} by {brand}"],
        "styles": ["Runner", "Classic", "Sport", "Casual", "Performance"],
        "features": [
            "Memory foam insole", "Breathable mesh", "Slip-resistant sole",
            "Arch support", "Lightweight design", "Cushioned heel"
        ],
        "materials": ["Leather", "Synthetic", "Canvas", "Mesh", "Suede"],
        "sizes": ["7", "8", "9", "10", "11", "12", "13"],
        "specs_ranges": {"price": (59, 249)}
    }
}

HOME_GARDEN_TEMPLATES = {
    "Furniture": {
        "brands": ["HomeStyle", "ComfortLiving", "ModernSpace", "CraftWood", "UrbanHome"],
        "name_patterns": ["{brand} {style} {item}", "{style} {item} Collection"],
        "styles": ["Modern", "Classic", "Minimalist", "Rustic", "Contemporary"],
        "items": ["Sofa", "Dining Table", "Bookshelf", "Coffee Table", "Armchair"],
        "features": [
            "Solid wood construction", "Easy assembly", "Stain-resistant fabric",
            "Adjustable height", "Hidden storage", "Eco-friendly materials"
        ],
        "materials": ["Oak", "Walnut", "Pine", "MDF", "Steel", "Velvet", "Leather"],
        "specs_ranges": {
            "weight_capacity": (200, 500),
            "price": (199, 2499)
        }
    },
    "Kitchen Appliances": {
        "brands": ["KitchenPro", "ChefMaster", "HomeCook", "CulinArt", "SmartChef"],
        "name_patterns": ["{brand} {type} {version}", "Pro {type} by {brand}"],
        "types": ["Blender", "Coffee Maker", "Air Fryer", "Stand Mixer", "Toaster"],
        "features": [
            "10 speed settings", "Dishwasher safe parts", "Digital display",
            "Timer function", "Stainless steel construction", "Quiet operation"
        ],
        "specs_ranges": {
            "power_watts": (500, 1500),
            "capacity_liters": (1, 6),
            "price": (49, 499)
        }
    }
}

BEAUTY_TEMPLATES = {
    "Skincare": {
        "brands": ["GlowSkin", "PureDerm", "NaturalGlow", "SkinScience", "RadiantYou"],
        "name_patterns": ["{brand} {type} {benefit}", "{benefit} {type} Serum"],
        "types": ["Serum", "Moisturizer", "Cleanser", "Toner", "Eye Cream"],
        "benefits": ["Anti-Aging", "Hydrating", "Brightening", "Revitalizing", "Firming"],
        "features": [
            "Hyaluronic acid", "Vitamin C enriched", "Paraben-free",
            "Cruelty-free", "Dermatologist tested", "For all skin types"
        ],
        "ingredients": ["Hyaluronic Acid", "Retinol", "Vitamin C", "Niacinamide", "Peptides"],
        "specs_ranges": {
            "size_ml": (15, 100),
            "price": (19, 149)
        }
    },
    "Fragrances": {
        "brands": ["ScentLux", "AromaElite", "PerfumeHouse", "EssenceArt", "FragrancePro"],
        "name_patterns": ["{brand} {mood}", "{mood} by {brand}"],
        "moods": ["Midnight", "Fresh", "Ocean", "Bloom", "Noir", "Velvet"],
        "features": [
            "Long-lasting scent", "Premium ingredients", "Elegant bottle design",
            "Gift-ready packaging", "Travel-friendly size"
        ],
        "notes": ["Top notes: Citrus", "Heart notes: Floral", "Base notes: Musk"],
        "specs_ranges": {
            "size_ml": (30, 100),
            "price": (49, 199)
        }
    }
}

SPORTS_TEMPLATES = {
    "Equipment": {
        "brands": ["SportMax", "AthletePro", "FitGear", "ActiveLife", "PowerFit"],
        "name_patterns": ["{brand} {type} {version}", "Pro {type} by {brand}"],
        "types": ["Yoga Mat", "Dumbbells", "Resistance Bands", "Jump Rope", "Foam Roller"],
        "features": [
            "Non-slip surface", "Eco-friendly materials", "Durable construction",
            "Easy to clean", "Portable design", "Multiple resistance levels"
        ],
        "materials": ["Natural rubber", "TPE", "Neoprene", "Steel", "PVC-free foam"],
        "specs_ranges": {
            "price": (19, 199)
        }
    },
    "Athletic Apparel": {
        "brands": ["ActiveWear", "FitStyle", "SportFlex", "MovePro", "AthleticEdge"],
        "name_patterns": ["{brand} {type} {style}", "{style} {type}"],
        "types": ["Running Shorts", "Sports Bra", "Leggings", "Tank Top", "Track Jacket"],
        "styles": ["Performance", "Comfort", "Pro", "Essential", "Elite"],
        "features": [
            "4-way stretch", "Moisture-wicking", "Quick-dry fabric",
            "Flatlock seams", "Hidden pocket", "UV protection"
        ],
        "materials": ["Polyester", "Spandex", "Nylon", "Recycled materials"],
        "sizes": ["XS", "S", "M", "L", "XL"],
        "specs_ranges": {"price": (29, 129)}
    }
}

# Combine all templates
CATEGORY_PRODUCT_TEMPLATES = {
    "Consumer Electronics": ELECTRONICS_TEMPLATES,
    "Fashion/Apparel": FASHION_TEMPLATES,
    "Home & Garden": HOME_GARDEN_TEMPLATES,
    "Beauty & Personal Care": BEAUTY_TEMPLATES,
    "Sports & Outdoors": SPORTS_TEMPLATES
}


# ============== Content Generation Templates ==============

DESCRIPTION_TEMPLATES = {
    "excellent": [
        "Introducing the {name}, a {adjective} {category_item} designed for {audience}. "
        "Featuring {feature1} and {feature2}, this {category_item} delivers {benefit}. "
        "Crafted with {material}, it offers {value_prop}. "
        "The {name} comes with {warranty} and is available in {colors}.",

        "Discover the {name} - where {quality} meets {innovation}. "
        "This {category_item} features {feature1}, {feature2}, and {feature3}. "
        "Built with premium {material}, it's designed to {purpose}. "
        "With {specs}, you get {benefit} in every use."
    ],
    "good": [
        "The {name} is a {adjective} {category_item} with {feature1} and {feature2}. "
        "Made from {material}, it provides {benefit}. "
        "Available in {colors} with {warranty}.",

        "Meet the {name}, featuring {feature1} and {feature2}. "
        "This {category_item} offers {benefit} for {audience}. "
        "Includes {warranty}."
    ],
    "acceptable": [
        "The {name} has {feature1}. It's made of {material}. "
        "Good for {purpose}. Comes in {colors}.",

        "{name} - a {category_item} with {feature1}. "
        "{benefit}. Available now."
    ],
    "poor": [
        "{name} is great. Best product ever! Revolutionary design that changes everything. "
        "You won't believe how amazing this is. Buy now!",

        "This {category_item} is the best in class. World's first {feature1}. "
        "Unbeatable quality at this price. Get yours today!"
    ]
}

MARKETING_COPY_TEMPLATES = {
    "excellent": [
        "Transform your {experience} with the {name}. Our {adjective} {category_item} "
        "combines {feature1} with {feature2} to deliver an unmatched experience. "
        "Whether you're {use_case1} or {use_case2}, the {name} adapts to your needs. "
        "Join thousands of satisfied customers who have made the switch.",

        "Experience the difference with {name}. Designed with {audience} in mind, "
        "this {category_item} features {feature1} for {benefit1} and {feature2} for {benefit2}. "
        "Every detail has been carefully considered to ensure you get the most out of your purchase."
    ],
    "good": [
        "The {name} brings you {feature1} and {feature2}. Perfect for {audience}, "
        "this {category_item} helps you {benefit}. Upgrade your {experience} today.",

        "Looking for a reliable {category_item}? The {name} offers {feature1} "
        "at an excellent value. Designed for {purpose}."
    ],
    "acceptable": [
        "{name} has {feature1}. Good for {purpose}. Try it now.",

        "Buy the {name}. It has {feature1} and works well."
    ],
    "poor": [
        "AMAZING DEAL! {name} is the BEST {category_item} on the market! "
        "Don't miss out on this incredible offer! Limited time only!",

        "This product is revolutionary and game-changing. "
        "Best in class quality. Unbeatable. Buy now before it's gone!"
    ]
}

FEATURE_BULLET_TEMPLATES = {
    "excellent": {
        "count": (5, 7),
        "templates": [
            "{feature} for enhanced {benefit}",
            "Premium {material} construction ensures {durability}",
            "{spec_value} {spec_unit} {spec_type} delivers {performance}",
            "Designed for {use_case} with {feature}",
            "{warranty} included for peace of mind"
        ]
    },
    "good": {
        "count": (4, 6),
        "templates": [
            "{feature}",
            "Made with {material}",
            "{spec_value} {spec_unit} {spec_type}",
            "Great for {use_case}",
            "Includes {warranty}"
        ]
    },
    "acceptable": {
        "count": (2, 4),
        "templates": [
            "{feature}",
            "{material} material",
            "{spec_type}: {spec_value}"
        ]
    },
    "poor": {
        "count": (1, 3),
        "templates": [
            "Best {feature} ever",
            "Revolutionary technology",
            "Unbeatable quality"
        ]
    }
}

META_DESCRIPTION_TEMPLATES = {
    "excellent": [
        "Shop the {name} - {adjective} {category_item} featuring {feature1} and {feature2}. "
        "Free shipping on orders over $50. {warranty} included.",
        "Discover {name}: {feature1}, {feature2}, premium {material}. "
        "Perfect for {audience}. Shop now with free returns."
    ],
    "good": [
        "Buy {name} with {feature1}. {category_item} for {audience}. Free shipping available.",
        "{name} - {feature1} and {feature2}. Shop {brand} {category_item} today."
    ],
    "acceptable": [
        "{name} - {category_item}. Buy now.",
        "Shop {name}. Good {category_item}."
    ],
    "poor": [
        "{name}",
        "Buy this amazing product now! Best deal ever! Don't miss out on this incredible offer that will change your life forever!"
    ]
}


# ============== Defect Injection ==============

ACCURACY_DEFECTS = [
    {"type": "wrong_dimension", "field": "display_size", "modification": lambda x: x + random.uniform(0.2, 0.5)},
    {"type": "wrong_weight", "field": "weight", "modification": lambda x: x + random.randint(5, 20)},
    {"type": "wrong_price", "field": "price", "modification": lambda x: x * random.uniform(0.85, 0.95)},
    {"type": "invented_feature", "add": "AI-powered quantum processing"},
    {"type": "wrong_material", "replace": {"Aluminum": "Plastic", "Leather": "Synthetic"}},
]

BRAND_VOICE_DEFECTS = [
    {"type": "prohibited_phrase", "phrases": ["best in class", "world's first", "revolutionary", "game-changing", "unbeatable"]},
    {"type": "wrong_person", "changes": {"you": "customers", "your": "their"}},
    {"type": "informal_tone", "changes": {"excellent": "super cool", "premium": "awesome"}},
]

READABILITY_DEFECTS = [
    {"type": "long_sentence", "min_words": 45},
    {"type": "passive_voice", "templates": [
        "The product is designed by experts",
        "Features are included that provide",
        "Quality is ensured by our team"
    ]},
    {"type": "jargon", "terms": [
        "synergistic functionality", "paradigm-shifting innovation",
        "holistic approach to optimization", "leveraging core competencies"
    ]},
]


class SyntheticDataGenerator:
    """Generates synthetic product data, content, and metrics for testing."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize the generator with optional seed for reproducibility."""
        if seed:
            random.seed(seed)
            Faker.seed(seed)
        self.fake = Faker()

    def generate_product_id(self) -> str:
        """Generate a unique product ID."""
        return f"SKU-{random.randint(10000, 99999)}"

    def generate_content_id(self, product_id: str, version: int) -> str:
        """Generate a content version ID."""
        return f"{product_id}-v{version}"

    def generate_specifications(
        self,
        category: str,
        subcategory: str,
        template: Dict
    ) -> Dict[str, Any]:
        """Generate product specifications based on category template."""
        specs = {}

        # Generate name
        brand = random.choice(template["brands"])
        if "name_patterns" in template:
            pattern = random.choice(template["name_patterns"])
            name = pattern.format(
                brand=brand,
                version=random.randint(1, 15),
                adjective=random.choice(template.get("adjectives", ["Premium"])),
                item=random.choice(template.get("items", template.get("types", ["Item"]))),
                style=random.choice(template.get("styles", ["Classic"])),
                mood=random.choice(template.get("moods", ["Fresh"]))
            )
        else:
            name = f"{brand} Product {random.randint(100, 999)}"

        specs["name"] = name
        specs["brand"] = brand

        # Generate dimensions based on category
        if category == "Consumer Electronics":
            if subcategory == "Smartphones":
                specs["dimensions"] = {
                    "length": round(random.uniform(5.8, 6.9), 1),
                    "width": round(random.uniform(2.6, 3.2), 1),
                    "height": round(random.uniform(0.28, 0.35), 2),
                    "unit": "inches"
                }
                specs["weight"] = {
                    "value": random.randint(150, 240),
                    "unit": "grams"
                }
            elif subcategory == "Laptops":
                specs["dimensions"] = {
                    "length": round(random.uniform(11, 14), 1),
                    "width": round(random.uniform(8, 10), 1),
                    "height": round(random.uniform(0.4, 0.8), 2),
                    "unit": "inches"
                }
                specs["weight"] = {
                    "value": round(random.uniform(1.2, 2.5), 1),
                    "unit": "kg"
                }

        # Add features
        if "features" in template:
            num_features = random.randint(4, 7)
            specs["features"] = random.sample(template["features"], min(num_features, len(template["features"])))

        # Add materials
        if "materials" in template:
            num_materials = random.randint(1, 3)
            specs["materials"] = random.sample(template["materials"], min(num_materials, len(template["materials"])))

        # Add colors
        if "colors" in template:
            specs["colors"] = random.sample(template["colors"], random.randint(2, 4))
        else:
            specs["colors"] = random.sample(
                ["Black", "White", "Silver", "Gold", "Blue", "Red", "Green"],
                random.randint(2, 4)
            )

        # Add price
        if "specs_ranges" in template and "price" in template["specs_ranges"]:
            price_range = template["specs_ranges"]["price"]
            specs["price"] = round(random.uniform(price_range[0], price_range[1]), 2)
        else:
            specs["price"] = round(random.uniform(49, 999), 2)

        # Add warranty
        specs["warranty"] = random.choice([
            "1 year limited warranty",
            "2 year manufacturer warranty",
            "90-day warranty",
            "Lifetime warranty"
        ])

        # Add sizes for applicable categories
        if "sizes" in template:
            specs["sizes_available"] = template["sizes"]

        # Add category-specific specs
        if "specs_ranges" in template:
            for spec_name, spec_range in template["specs_ranges"].items():
                if spec_name != "price" and spec_name not in specs:
                    if isinstance(spec_range, tuple):
                        specs[spec_name] = round(random.uniform(spec_range[0], spec_range[1]), 1)

        return specs

    def generate_content(
        self,
        specifications: Dict[str, Any],
        quality_level: str,
        category: str,
        inject_defects: bool = True
    ) -> Dict[str, Any]:
        """Generate content for a product at specified quality level."""
        content = {}

        # Get templates for quality level
        desc_templates = DESCRIPTION_TEMPLATES.get(quality_level, DESCRIPTION_TEMPLATES["acceptable"])
        marketing_templates = MARKETING_COPY_TEMPLATES.get(quality_level, MARKETING_COPY_TEMPLATES["acceptable"])
        bullet_config = FEATURE_BULLET_TEMPLATES.get(quality_level, FEATURE_BULLET_TEMPLATES["acceptable"])
        meta_templates = META_DESCRIPTION_TEMPLATES.get(quality_level, META_DESCRIPTION_TEMPLATES["acceptable"])

        # Prepare substitution values
        name = specifications.get("name", "Product")
        brand = specifications.get("brand", "Brand")
        features = specifications.get("features", ["feature"])
        materials = specifications.get("materials", ["material"])
        colors = ", ".join(specifications.get("colors", ["various colors"])[:3])
        warranty = specifications.get("warranty", "standard warranty")
        price = specifications.get("price", 99.99)

        subs = {
            "name": name,
            "brand": brand,
            "adjective": random.choice(["premium", "innovative", "exceptional", "reliable", "versatile"]),
            "category_item": category.lower().replace("/", " "),
            "feature1": features[0] if features else "advanced features",
            "feature2": features[1] if len(features) > 1 else "modern design",
            "feature3": features[2] if len(features) > 2 else "quality construction",
            "material": materials[0] if materials else "quality materials",
            "colors": colors,
            "warranty": warranty,
            "benefit": random.choice(["exceptional performance", "unmatched quality", "outstanding value", "superior experience"]),
            "value_prop": random.choice(["excellent value", "lasting quality", "dependable performance"]),
            "audience": random.choice(["professionals", "everyday users", "enthusiasts", "families"]),
            "quality": random.choice(["craftsmanship", "innovation", "design"]),
            "innovation": random.choice(["technology", "functionality", "style"]),
            "purpose": random.choice(["enhance your daily routine", "meet your needs", "exceed expectations"]),
            "specs": f"${price:.2f}" if price else "competitive pricing",
            "experience": random.choice(["daily routine", "lifestyle", "activities"]),
            "use_case1": random.choice(["working from home", "on the go", "relaxing"]),
            "use_case2": random.choice(["traveling", "exercising", "entertaining"]),
            "benefit1": random.choice(["comfort", "convenience", "efficiency"]),
            "benefit2": random.choice(["style", "durability", "performance"]),
            "use_case": random.choice(["everyday use", "professional settings", "active lifestyles"]),
            "durability": random.choice(["long-lasting use", "years of service", "reliable performance"]),
            "spec_value": str(random.randint(10, 100)),
            "spec_unit": random.choice(["hours", "watts", "mm"]),
            "spec_type": random.choice(["battery life", "power", "size"]),
            "performance": random.choice(["optimal results", "peak performance", "consistent quality"])
        }

        # Generate description
        desc_template = random.choice(desc_templates)
        content["description"] = desc_template.format(**subs)

        # Generate marketing copy
        marketing_template = random.choice(marketing_templates)
        content["marketing_copy"] = marketing_template.format(**subs)

        # Generate feature bullets
        bullet_count = random.randint(bullet_config["count"][0], bullet_config["count"][1])
        bullets = []
        for i in range(bullet_count):
            template = random.choice(bullet_config["templates"])
            bullet = template.format(**subs)
            bullets.append(bullet)
        content["feature_bullets"] = bullets

        # Generate meta description
        meta_template = random.choice(meta_templates)
        content["meta_description"] = meta_template.format(**subs)

        # Inject defects for poor/acceptable quality
        if inject_defects and quality_level in ["poor", "acceptable"]:
            content = self._inject_defects(content, specifications, quality_level)

        return content

    def _inject_defects(
        self,
        content: Dict[str, Any],
        specifications: Dict[str, Any],
        quality_level: str
    ) -> Dict[str, Any]:
        """Inject defects into content based on quality level."""
        defect_probability = 0.7 if quality_level == "poor" else 0.4

        # Inject accuracy defects
        if random.random() < defect_probability:
            defect = random.choice(ACCURACY_DEFECTS)
            if defect["type"] == "invented_feature":
                content["description"] += f" Features {defect['add']}."
            elif defect["type"] == "wrong_dimension" and "dimensions" in specifications:
                dims = specifications["dimensions"]
                if "length" in dims:
                    wrong_dim = round(dims["length"] + random.uniform(0.2, 0.5), 1)
                    content["description"] = content["description"].replace(
                        str(dims["length"]),
                        str(wrong_dim)
                    )

        # Inject brand voice defects
        if random.random() < defect_probability:
            defect = random.choice(BRAND_VOICE_DEFECTS)
            if defect["type"] == "prohibited_phrase":
                phrase = random.choice(defect["phrases"])
                content["marketing_copy"] = f"This {phrase} product " + content["marketing_copy"]

        # Inject readability defects
        if random.random() < defect_probability:
            defect = random.choice(READABILITY_DEFECTS)
            if defect["type"] == "jargon":
                term = random.choice(defect["terms"])
                content["description"] += f" Our {term} ensures superior results."
            elif defect["type"] == "passive_voice":
                passive = random.choice(defect["templates"])
                content["description"] += f" {passive}."

        return content

    def generate_product(
        self,
        category: Optional[str] = None,
        quality_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a complete product with specifications and content."""
        # Select category
        if not category:
            category = random.choice(list(CATEGORY_PRODUCT_TEMPLATES.keys()))

        # Select subcategory
        subcategories = list(CATEGORY_PRODUCT_TEMPLATES[category].keys())
        subcategory = random.choice(subcategories)
        template = CATEGORY_PRODUCT_TEMPLATES[category][subcategory]

        # Determine quality level
        if not quality_level:
            quality_level = self._select_quality_level()

        # Generate product ID
        product_id = self.generate_product_id()

        # Generate specifications
        specifications = self.generate_specifications(category, subcategory, template)

        # Generate content versions
        generated_content = {}
        for version in range(1, random.randint(2, 4)):
            version_quality = quality_level if version == 1 else self._select_quality_level()
            content = self.generate_content(specifications, version_quality, category)

            generated_content[f"version_{version}"] = {
                "prompt_used": f"Write a {version_quality} quality product description for a {subcategory.lower()}...",
                "model": random.choice(["claude-3-sonnet", "claude-3-opus", "gpt-4"]),
                "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat() + "Z",
                "quality_level": version_quality,
                **content
            }

        return {
            "product_id": product_id,
            "category": category,
            "subcategory": subcategory,
            "brand": specifications["brand"],
            "specifications": specifications,
            "generated_content": generated_content
        }

    def _select_quality_level(self) -> str:
        """Select a quality level based on distribution."""
        rand = random.random()
        cumulative = 0
        for level, config in [
            ("excellent", 0.20),
            ("good", 0.35),
            ("acceptable", 0.25),
            ("poor", 0.20)
        ]:
            cumulative += config
            if rand < cumulative:
                return level
        return "acceptable"

    def generate_translations(
        self,
        content: Dict[str, Any],
        target_languages: List[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Generate simulated translations for content."""
        if not target_languages:
            target_languages = ["fr-CA", "es", "de"]

        translations = {}

        for lang in target_languages:
            # Simulate translation by adding language-specific modifications
            trans_content = {}

            # For simulation, we'll just add language markers
            # In production, this would be actual translated content
            for field in ["description", "marketing_copy", "meta_description"]:
                if field in content:
                    trans_content[field] = f"[{lang.upper()}] {content[field]}"

            if "feature_bullets" in content:
                trans_content["feature_bullets"] = [
                    f"[{lang.upper()}] {bullet}" for bullet in content["feature_bullets"]
                ]

            translations[lang] = trans_content

        return translations

    def generate_human_review(
        self,
        content_id: str,
        auto_score: float
    ) -> Dict[str, Any]:
        """Generate simulated human review data."""
        # Human scores tend to correlate with auto scores but with some variance
        base_score = auto_score / 20  # Convert 0-100 to 1-5 scale
        variance = random.uniform(-0.5, 0.5)

        def clamp_score(score: float) -> int:
            return max(1, min(5, round(score + variance)))

        review = {
            "review_id": f"REV-{uuid.uuid4().hex[:8]}",
            "content_id": content_id,
            "reviewer_id": f"reviewer_{random.randint(1, 10):02d}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "scores": {
                "accuracy": clamp_score(base_score),
                "completeness": clamp_score(base_score + random.uniform(-0.3, 0.3)),
                "brand_voice": clamp_score(base_score + random.uniform(-0.5, 0.5)),
                "readability": clamp_score(base_score + random.uniform(-0.3, 0.3)),
                "seo": clamp_score(base_score + random.uniform(-0.3, 0.3)),
                "overall": clamp_score(base_score)
            },
            "annotations": [],
            "verdict": self._determine_verdict(auto_score),
            "improvement_notes": "",
            "review_duration_seconds": random.randint(60, 300)
        }

        # Add annotations for lower scores
        if auto_score < 70:
            review["annotations"] = self._generate_annotations(auto_score)
            review["improvement_notes"] = "Please address the noted issues before publishing."

        return review

    def _determine_verdict(self, score: float) -> str:
        """Determine review verdict based on score."""
        if score >= 85:
            return "approve"
        elif score >= 60:
            return "conditional_approve"
        else:
            return "reject"

    def _generate_annotations(self, score: float) -> List[Dict[str, Any]]:
        """Generate sample annotations for review."""
        annotation_templates = [
            {
                "type": "accuracy_error",
                "severity": "major",
                "span": {"start": 45, "end": 67},
                "original_text": "6.5-inch display",
                "correction": "6.7-inch display",
                "comment": "Display size incorrect per specifications"
            },
            {
                "type": "brand_voice_issue",
                "severity": "minor",
                "span": {"start": 120, "end": 145},
                "original_text": "best in class",
                "correction": "industry-leading",
                "comment": "Prohibited phrase - use approved alternatives"
            },
            {
                "type": "style_issue",
                "severity": "minor",
                "span": {"start": 200, "end": 280},
                "original_text": "This is a very long sentence that goes on and on...",
                "correction": "Split into shorter sentences",
                "comment": "Sentence exceeds 25 word limit"
            }
        ]

        # Return more annotations for lower scores
        num_annotations = max(1, int((100 - score) / 20))
        return random.sample(annotation_templates, min(num_annotations, len(annotation_templates)))

    def generate_performance_metrics(
        self,
        content_id: str,
        quality_score: float
    ) -> Dict[str, Any]:
        """Generate simulated performance metrics correlated with quality score."""
        # Base metrics influenced by quality score
        quality_factor = quality_score / 100

        # Traffic metrics
        base_impressions = random.randint(5000, 25000)
        impressions = int(base_impressions * (0.7 + 0.6 * quality_factor))
        base_ctr = 3 + 4 * quality_factor + random.uniform(-1, 1)
        clicks = int(impressions * base_ctr / 100)

        # Engagement metrics
        page_views = int(clicks * random.uniform(0.7, 0.9))
        base_time = 60 + 120 * quality_factor
        avg_time = int(base_time + random.randint(-20, 40))
        bounce_rate = 60 - 30 * quality_factor + random.uniform(-5, 5)
        scroll_depth = 40 + 40 * quality_factor + random.uniform(-10, 10)

        # Conversion metrics
        base_atc_rate = 5 + 10 * quality_factor + random.uniform(-2, 2)
        add_to_cart = int(page_views * base_atc_rate / 100)
        conv_rate = 2 + 5 * quality_factor + random.uniform(-1, 1)
        purchases = int(add_to_cart * conv_rate / 10)
        avg_order = random.uniform(50, 200)
        revenue = purchases * avg_order

        return {
            "content_id": content_id,
            "performance_period": f"{(datetime.utcnow() - timedelta(days=30)).strftime('%Y-%m-%d')} to {datetime.utcnow().strftime('%Y-%m-%d')}",
            "traffic_metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(clicks / impressions * 100, 2) if impressions > 0 else 0,
                "avg_position": round(10 - 6 * quality_factor + random.uniform(-1, 1), 1)
            },
            "engagement_metrics": {
                "page_views": page_views,
                "avg_time_on_page": avg_time,
                "bounce_rate": round(max(20, min(80, bounce_rate)), 1),
                "scroll_depth": round(max(30, min(95, scroll_depth)), 0)
            },
            "conversion_metrics": {
                "add_to_cart": add_to_cart,
                "add_to_cart_rate": round(max(1, base_atc_rate), 2),
                "purchases": purchases,
                "conversion_rate": round(max(0.5, conv_rate), 2),
                "revenue": round(revenue, 2)
            },
            "content_quality_score": quality_score
        }

    def generate_brand_guidelines(self, brand_name: str = "TechBrand") -> Dict[str, Any]:
        """Generate sample brand guidelines."""
        return {
            "brand_name": brand_name,
            "voice_attributes": {
                "tone": "professional yet approachable",
                "personality": ["innovative", "reliable", "premium"],
                "perspective": "second person (you/your)"
            },
            "terminology": {
                "preferred": {
                    "smartphone": "device",
                    "buy": "get yours",
                    "features": "capabilities",
                    "cheap": "affordable",
                    "product": "solution"
                },
                "prohibited": [
                    "cheap", "budget", "best in class", "world's first",
                    "revolutionary", "game-changing", "unbeatable",
                    "unprecedented", "groundbreaking"
                ]
            },
            "style_rules": {
                "sentence_length": {"max": 25, "ideal": 15},
                "paragraph_length": {"max": 4, "ideal": 2},
                "bullets_per_list": {"min": 3, "max": 7},
                "capitalization": "sentence case for descriptions",
                "numbers": "spell out 1-9, use digits for 10+"
            },
            "seo_requirements": {
                "title_max_length": 60,
                "meta_description_length": {"min": 120, "max": 160},
                "primary_keywords": ["smartphone", "mobile", "device", "technology"],
                "keyword_density": {"min": 1, "max": 3}
            }
        }

    def generate_dataset(
        self,
        num_products: int = 100,
        include_translations: bool = True,
        include_reviews: bool = True,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """Generate a complete dataset for testing."""
        products = []
        reviews = []
        metrics = []

        for _ in range(num_products):
            product = self.generate_product()

            # Add translations
            if include_translations:
                for version_key, version_content in product["generated_content"].items():
                    product["generated_content"][version_key]["translations"] = \
                        self.generate_translations(version_content)

            products.append(product)

            # Generate reviews and metrics for each content version
            for version_key, version_content in product["generated_content"].items():
                content_id = f"{product['product_id']}-{version_key}"

                # Estimate quality score based on quality level
                quality_level = version_content.get("quality_level", "acceptable")
                quality_scores = {
                    "excellent": random.uniform(85, 98),
                    "good": random.uniform(70, 85),
                    "acceptable": random.uniform(55, 70),
                    "poor": random.uniform(30, 55)
                }
                quality_score = quality_scores.get(quality_level, 60)

                if include_reviews:
                    review = self.generate_human_review(content_id, quality_score)
                    reviews.append(review)

                if include_metrics:
                    metric = self.generate_performance_metrics(content_id, quality_score)
                    metrics.append(metric)

        return {
            "products": products,
            "human_reviews": reviews if include_reviews else [],
            "performance_metrics": metrics if include_metrics else [],
            "brand_guidelines": self.generate_brand_guidelines(),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_products": len(products),
            "total_content_versions": sum(len(p["generated_content"]) for p in products)
        }


def generate_sample_data(output_path: str = "data/sample_products.json", num_products: int = 100):
    """Generate and save sample data to a JSON file."""
    generator = SyntheticDataGenerator(seed=42)
    dataset = generator.generate_dataset(num_products=num_products)

    with open(output_path, "w") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated {dataset['total_products']} products with {dataset['total_content_versions']} content versions")
    return dataset


if __name__ == "__main__":
    generate_sample_data()
