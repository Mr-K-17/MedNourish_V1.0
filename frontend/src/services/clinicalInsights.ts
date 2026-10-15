/**
 * Clinical Insights & Dataset Knowledge Mapping (MedNourish V3).
 *
 * Provides structured educational clinical intelligence based on curated reference datasets:
 * - Major Causes / Etiology / Risk Factors
 * - Clinical Medication & Pharmacological Reference (strictly framed as physician-prescribed reference)
 * - Biological Reasoning Chain (pathophysiological rationale for why symptoms occur)
 */

export interface ClinicalInsight {
  nutrientName: string;
  deficiencyTitle: string;
  majorCauses: string[];
  medications: string[];
  reasoning: string;
  affectedRegions: string[];
}

const CLINICAL_INSIGHTS_DB: Record<string, ClinicalInsight> = {
  'vitamin a': {
    nutrientName: 'Vitamin A (Retinol & Carotenoids)',
    deficiencyTitle: 'Vitamin A Deficiency & Ocular Xerophthalmia',
    majorCauses: [
      'Low dietary intake of animal sources (liver, egg yolks, whole milk) or provitamin carotenoids (carrots, sweet potatoes, spinach)',
      'Impaired fat absorption (celiac disease, chronic pancreatitis, cystic fibrosis, biliary obstruction)',
      'Chronic alcohol consumption impairing hepatic zinc and retinol dehydrogenase activity',
      'Increased metabolic demand during childhood growth, pregnancy, or post-infection convalescence',
    ],
    medications: [
      'Oral Retinol Palmitate (200,000 IU single dose or divided therapeutic regimens under clinician supervision)',
      'Water-miscible Vitamin A formulations for patients with severe pancreatic or biliary malabsorption',
      'Artificial tear lubricants and preservative-free ocular ointments for corneal xerosis protection',
    ],
    reasoning:
      'Vitamin A is the essential biochemical precursor to 11-cis-retinal, which binds opsin to form rhodopsin (the visual pigment in retinal rods responsible for scotopic vision). Lack of retinal impairs rod recovery in dim illumination, leading to night blindness. Concurrently, retinol is vital for maintaining mucus-secreting goblet cells; its absence triggers squamous metaplasia and keratinization of the ocular and cutaneous epithelia, producing Bitot spots, conjunctival xerosis, and dry follicular hyperkeratosis (phrynoderma).',
    affectedRegions: ['Eyes', 'Skin', 'Immune System'],
  },
  'vitamin b12': {
    nutrientName: 'Vitamin B12 (Cobalamin)',
    deficiencyTitle: 'Vitamin B12 Deficiency & Pernicious Anemia',
    majorCauses: [
      'Strict unsupplemented vegetarian or vegan diet lacking animal-derived cobalamin',
      'Autoimmune pernicious anemia (anti-intrinsic factor or anti-parietal cell antibodies)',
      'Atrophic gastritis, prolonged use of proton pump inhibitors (PPIs) or metformin reducing gastric acid required to cleave cobalamin from food proteins',
      'Terminal ileal resection, Crohn’s disease, or ileal malabsorption preventing intrinsic factor-B12 uptake',
    ],
    medications: [
      'Intramuscular Cyanocobalamin / Hydroxocobalamin (1,000 mcg weekly for 4-6 weeks, followed by monthly maintenance)',
      'High-dose Oral Methylcobalamin / Cyanocobalamin (1,000 to 2,000 mcg daily for mild to moderate non-malabsorptive deficiency)',
      'Sublingual Methylcobalamin lozenges for individuals with partial oral absorption limitations',
    ],
    reasoning:
      'Vitamin B12 serves as an obligatory cofactor for methionine synthase (homocysteine to methionine) and L-methylmalonyl-CoA mutase. Cobalamin deficiency causes intracellular folate trapping, impairing DNA synthesis in rapidly dividing hematopoietic cells and resulting in megaloblastic macrocytic anemia. Simultaneously, failure of myelin sheath synthesis and accumulation of methylmalonic acid produce subacute combined degeneration of the spinal cord, peripheral neuropathies (tingling/numbness), and mucosal atrophy of the tongue (Hunter’s glossitis).',
    affectedRegions: ['Tongue', 'Nervous System', 'Blood (RBCs)', 'Lips'],
  },
  'vitamin c': {
    nutrientName: 'Vitamin C (Ascorbic Acid)',
    deficiencyTitle: 'Vitamin C Deficiency & Scurvy Syndrome',
    majorCauses: [
      'Prolonged absence of fresh citrus fruits, berries, peppers, and green vegetables in daily meals',
      'Excessive boiling, canning, or heat processing that thermal-degrades water-soluble ascorbic acid',
      'Chronic cigarette smoking and tobacco use (depletes systemic ascorbic acid pool by 30-50%)',
      'Severe anorexia, alcohol dependence, or restrictive elderly solitary diets',
    ],
    medications: [
      'Oral Ascorbic Acid (100 mg to 500 mg daily in divided doses until clinical resolution)',
      'Parenteral Sodium Ascorbate injections for severe clinical scurvy with hemorrhagic complications',
      'Buffered Calcium Ascorbate formulations for patients with gastric acid sensitivity',
    ],
    reasoning:
      'Ascorbic acid acts as an electron donor and reducing agent essential for prolyl and lysyl hydroxylase enzymes. These enzymes hydroxylate proline and lysine residues required for cross-linking the triple helix of collagen. In deficiency, defective collagen triple helices cannot maintain vascular endothelial basement membrane integrity, leading to fragile capillary walls, bleeding gums, perifollicular petechiae, corkscrew hairs, impaired wound healing, and subperiosteal hemorrhages.',
    affectedRegions: ['Gums / Mouth', 'Skin', 'Capillaries', 'Hair'],
  },
  'vitamin d': {
    nutrientName: 'Vitamin D (Cholecalciferol & Ergocalciferol)',
    deficiencyTitle: 'Vitamin D Deficiency & Hypocalcemic Osteomalacia',
    majorCauses: [
      'Minimal cutaneous solar UVB exposure due to indoor sedentary lifestyles, high latitudes, or heavy covering garments',
      'High epidermal melanin concentration reducing cutaneous synthesis of cholecalciferol',
      'Chronic renal disease (impaired 1-alpha-hydroxylase activation to calcitriol) or hepatic failure',
      'Obesity with sequestration of lipophilic cholecalciferol into adipose tissue depots',
    ],
    medications: [
      'Oral Cholecalciferol (Vitamin D3) 60,000 IU weekly for 8 to 12 weeks, transitioning to 1,000–2,000 IU daily maintenance',
      'Calcitriol (1,25-dihydroxycholecalciferol) 0.25 to 0.50 mcg daily for renal osteodystrophy or severe hypoparathyroidism',
      'Elemental Calcium Carbonate or Citrate (500–1,000 mg daily) to accompany vitamin D therapy and prevent hungry bone syndrome',
    ],
    reasoning:
      'Cholecalciferol is hydroxylated in the liver to 25(OH)D and subsequently in renal tubules to 1,25(OH)2D (calcitriol). Calcitriol binds the nuclear VDR receptor, stimulating enterocyte transcription of calbindin and TRPV6 channels, which increases intestinal calcium and phosphorus absorption from ~15% to 40%. Deficiency causes compensatory secondary hyperparathyroidism, which resorbs skeletal calcium, inducing bone aches, osteomalacia, muscle weakness, and joint stiffness.',
    affectedRegions: ['Bones', 'Muscles', 'Immunity', 'Teeth'],
  },
  'folate': {
    nutrientName: 'Folate (Vitamin B9)',
    deficiencyTitle: 'Folate Deficiency & Macrocytic Anemia',
    majorCauses: [
      'Inadequate dietary intake of raw leafy vegetables, beans, lentils, and fortified grains',
      'Chronic alcoholism interfering with enterohepatic folate circulation and renal conservation',
      'Malabsorptive disorders (tropical sprue, celiac disease, inflammatory bowel disease)',
      'Medication antagonism (methotrexate, trimethoprim, sulfasalazine, antiepileptics)',
    ],
    medications: [
      'Oral Folic Acid (1 mg to 5 mg daily for 1 to 4 months until complete hematologic recovery)',
      'L-Methylfolate (5-MTHF) 7.5 to 15 mg daily for patients with documented MTHFR gene polymorphism',
      'Folinic Acid (Leucovorin Calcium) for rescue therapy in dihydrofolate reductase inhibition',
    ],
    reasoning:
      'Folate derivatives (tetrahydrofolate, THF) function as one-carbon carriers in the de novo synthesis of purines and thymidylate. Without adequate folate, thymidylate synthase cannot generate dTMP from dUMP, leading to uracil misincorporation into nuclear DNA, double-strand breaks, and nuclear-cytoplasmic dissociation. Rapidly dividing precursor erythroblasts fail to divide normally, resulting in macrocytic megaloblastic anemia, mucosal oral ulcerations, angular cheilitis, and debilitating systemic fatigue.',
    affectedRegions: ['Tongue', 'Lips', 'Blood (RBCs)', 'Nervous System'],
  },
  'iron': {
    nutrientName: 'Iron (Ferritin & Elemental Fe)',
    deficiencyTitle: 'Iron Deficiency & Microcytic Hypochromic Anemia',
    majorCauses: [
      'Chronic occult blood loss (gastrointestinal bleeding, peptic ulcers, colon polyps, heavy menstrual menorrhagia)',
      'High dietary intake of inhibitors (tannins in tea/coffee, phytates in unsoaked grains) without vitamin C synergists',
      'Decreased duodenal absorption (Helicobacter pylori gastritis, bariatric bypass, celiac disease)',
      'High physiological demands (rapid adolescent growth, pregnancy, prolonged intense athletic training)',
    ],
    medications: [
      'Oral Ferrous Ascorbate or Ferrous Sulfate (100 mg to 200 mg elemental iron daily in divided doses on an empty stomach)',
      'Iron Bisglycinate chelate formulations (gentle on stomach with lower incidence of gastrointestinal constipation)',
      'Intravenous Ferric Carboxymaltose or Iron Sucrose for rapid repletion in severe anemia or intestinal intolerance',
    ],
    reasoning:
      'Iron is the central coordination atom of the heme porphyrin ring within hemoglobin and myoglobin, facilitating oxygen binding and delivery to peripheral tissues, and forms the core of electron-transport cytochromes. Depleted iron stores exhaust erythroblast hemoglobin synthesis, causing circulating microcytic, hypochromic erythrocytes. Tissues suffer chronic hypoxia, leading to compensatory tachycardia, spoon-shaped brittle nails (koilonychia), paleness of conjunctiva and tongue, hair thinning, and pica cravings.',
    affectedRegions: ['Nails', 'Lips', 'Tongue', 'Eyes', 'Hair'],
  },
  'b-complex': {
    nutrientName: 'Vitamin B-Complex (B1, B2, B3, B6)',
    deficiencyTitle: 'Multi B-Vitamin Depletion & Mucocutaneous Syndrome',
    majorCauses: [
      'High consumption of refined carbohydrates, polished white rice, and sugars without whole grains',
      'Chronic alcohol intake causing thiamine (B1) and riboflavin (B2) transport inhibition',
      'Prolonged gastrointestinal infections, dysbiosis, or antibiotic treatment destroying gut synthesis',
      'Restricted unbalanced diets devoid of dairy, legumes, and green vegetables',
    ],
    medications: [
      'High-potency Therapeutic B-Complex Tablets (containing B1 50mg, B2 10mg, B3 50mg, B6 10mg)',
      'Riboflavin (Vitamin B2) 10 mg to 50 mg daily for angular stomatitis and cheilosis',
      'Nicotinamide / Niacinamide 100 mg daily for glossitis, pellagroid rashes, and mucosal inflammation',
    ],
    reasoning:
      'B vitamins serve as essential coenzymes (FMN/FAD from B2, NAD/NADP from B3, PLP from B6, TPP from B1) for the mitochondrial Krebs cycle, fatty acid oxidation, and amino acid metabolism. Mucosal epithelial tissues with rapid cellular turnover (tongue papillae, lip commissures) depend heavily on continuous coenzyme availability. Lack of B2 and B3 rapidly causes atrophic glossitis, painful bilateral fissures at the corners of the mouth (angular cheilitis), and scaly seborrheic dermatitis.',
    affectedRegions: ['Lips', 'Tongue', 'Skin', 'Nails'],
  },
};

const DEFAULT_INSIGHT: ClinicalInsight = {
  nutrientName: 'Essential Micronutrient Complex',
  deficiencyTitle: 'Nutritional Imbalance & Micronutrient Support',
  majorCauses: [
    'Unbalanced dietary patterns lacking colorful fruits, vegetables, legumes, and whole proteins',
    'Increased physiological stress, inadequate restorative sleep, or irregular meal schedules',
    'Suboptimal gastrointestinal absorption or minor gut dysbiosis',
  ],
  medications: [
    'Comprehensive Balanced Multivitamin & Mineral Formulation (RDA standard, taken with meals)',
    'Consult a registered clinical dietitian or physician for diagnostic serum micronutrient panel testing',
  ],
  reasoning:
    'Micronutrients act as fundamental biocatalysts in enzymatic reactions, cellular oxygenation, and tissue synthesis. When intake falls below daily metabolic expenditure, systemic reserves gradually deplete, triggering mild compensatory symptoms across skin, eyes, nails, or oral mucosa before progressing to overt clinical illness.',
  affectedRegions: ['General Body', 'Skin', 'Energy Systems'],
};

/**
 * Retrieves structured clinical insight for a given nutrient or deficiency string.
 */
export function getDeficiencyClinicalInsight(query: string): ClinicalInsight {
  if (!query) return DEFAULT_INSIGHT;
  const q = query.toLowerCase();

  if (q.includes('vitamin a') || q.includes('retinol') || q.includes('xerophthalmia') || q.includes('bitot')) {
    return CLINICAL_INSIGHTS_DB['vitamin a'];
  }
  if (q.includes('b12') || q.includes('cobalamin') || q.includes('pernicious')) {
    return CLINICAL_INSIGHTS_DB['vitamin b12'];
  }
  if (q.includes('vitamin c') || q.includes('ascorbic') || q.includes('scurvy')) {
    return CLINICAL_INSIGHTS_DB['vitamin c'];
  }
  if (q.includes('vitamin d') || q.includes('cholecalciferol') || q.includes('bone')) {
    return CLINICAL_INSIGHTS_DB['vitamin d'];
  }
  if (q.includes('folate') || q.includes('b9') || q.includes('folic')) {
    return CLINICAL_INSIGHTS_DB['folate'];
  }
  if (q.includes('iron') || q.includes('anemia') || q.includes('ferritin') || q.includes('koilonychia')) {
    return CLINICAL_INSIGHTS_DB['iron'];
  }
  if (q.includes('b-complex') || q.includes('b1') || q.includes('b2') || q.includes('b3') || q.includes('b6') || q.includes('cheilitis') || q.includes('glossitis')) {
    return CLINICAL_INSIGHTS_DB['b-complex'];
  }

  return DEFAULT_INSIGHT;
}
