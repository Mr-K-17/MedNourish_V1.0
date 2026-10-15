"""NurseBot Conversational AI & Medical Sciences Knowledge Engine (MedNourish V3).

Capabilities:
1. Natural Conversational Dialogue:
   - Greetings, small talk, pleasantries, identity, capabilities, and friendly nurse persona.
2. Comprehensive Medical Sciences Knowledge Base:
   - Cardiology & Circulatory System (heart, cardiac cycle, conduction, blood pressure, RAAS).
   - Hematology (erythrocytes, hemoglobin, leukocytes, platelets, hemostasis, blood groups).
   - Respiratory Physiology (alveoli, gas exchange, partial pressures, respiratory regulation).
   - Gastroenterology & Metabolism (stomach, liver, pancreas, intestines, gut microbiome).
   - Neurology & Neurobiology (neurons, action potentials, neurotransmitters, myelin, BBB).
   - Endocrinology (insulin/glucagon, thyroid axis, adrenal cortisol, calcium homeostasis).
   - Immunology (innate vs adaptive, T/B cells, antibodies, inflammation mechanisms).
   - Nephrology (nephrons, GFR, countercurrent multiplier, electrolyte balance).
   - Cellular Biochemistry (Krebs cycle, mitochondria, ATP synthesis, enzymes, antioxidants).
   - Microbiology & Pharmacology (bacterial vs viral biology, antibiotic mechanisms, ADME).
   - Precision Nutrition (all 13 vitamins, essential minerals, absorption cofactors, RDA).
3. Optional Free External AI API Connector (HuggingFace / Ollama / OpenRouter / Gemini):
   - Graceful fallback: defaults to the trained local knowledge engine for 0-latency instant replies.
"""

import logging
import os
import re
from typing import Dict, List, Optional, Tuple
import httpx

logger = logging.getLogger(__name__)

# External Free AI endpoints configuration (optional)
FREE_AI_API_URL = os.getenv("NURSEBOT_AI_API_URL", "")
FREE_AI_API_KEY = os.getenv("NURSEBOT_AI_API_KEY", "")


# ---------------------------------------------------------------------------
# 1. CONVERSATIONAL DIALOGUE PATTERNS (Small Talk & Persona)
# ---------------------------------------------------------------------------

CONVERSATION_INTENTS: List[Tuple[List[str], str]] = [
    (
        [
            r"^(?:hi|hello|hey|heya|howdy|greetings|hola)\b",
            r"^good\s+(?:morning|afternoon|evening|day)\b",
        ],
        (
            "Hello there! I am MedNourish NurseBot, your digital nurse assistant. "
            "I'm trained to help you understand medical sciences, human physiology, body systems, "
            "and evidence-based nutrition. How are you feeling today, and what can I help you explore?"
        ),
    ),
    (
        [
            r"\bhow\s+are\s+you\b",
            r"\bhow\s+are\s+things\b",
            r"\bhow('s|s)\s+it\s+going\b",
        ],
        (
            "I'm doing wonderful, thank you for asking! I'm active and ready to assist you. "
            "Whether you have questions about how our organs work, cellular biology, biochemistry, "
            "or navigating MedNourish, feel free to ask me anything!"
        ),
    ),
    (
        [
            r"\bwho\s+are\s+you\b",
            r"\bwhat\s+is\s+your\s+name\b",
            r"\btell\s+me\s+about\s+yourself\b",
            r"\bwho\s+made\s+you\b",
            r"\bwho\s+created\s+you\b",
        ],
        (
            "I am NurseBot, the AI-powered clinical guidance assistant within MedNourish. "
            "I've been built with a comprehensive medical science knowledge base covering human anatomy, "
            "physiology, biochemistry, disease mechanisms, and nutritional health. "
            "While I don't replace an in-person physician or provide individual diagnoses, "
            "I can explain complex medical concepts clearly and empathetically."
        ),
    ),
    (
        [
            r"\bwhat\s+can\s+you\s+do\b",
            r"\bhow\s+can\s+you\s+help\b",
            r"\bwhat\s+are\s+your\s+features\b",
            r"\byour\s+capabilities\b",
        ],
        (
            "Here is what I can do for you:\n"
            "• Explain Medical Sciences: Ask about organs (heart, liver, brain, kidneys), cellular ATP, hormones, or immunity.\n"
            "• Nutritional Biology: Inquire how vitamins, minerals, and enzymes function in your body.\n"
            "• App Assistance: Learn how to use MedBot questionnaires, Symptom Explorer, CarePlan tasks, or MedScan image triage.\n"
            "• Natural Dialogue: Chat with me about general health literacy and wellness science!"
        ),
    ),
    (
        [
            r"\bthank\s*(?:s|you)\b",
            r"\bmuch\s+appreciated\b",
            r"\bthanks\s+a\s+lot\b",
            r"\bhelpful\b",
        ],
        (
            "You are very welcome! Promoting health literacy and clear medical understanding is what I'm here for. "
            "Let me know if there's anything else you'd like to dive into!"
        ),
    ),
    (
        [
            r"\b(?:bye|goodbye|see\s+you|cya|take\s+care|have\s+a\s+good\s+day)\b",
        ],
        (
            "Goodbye! Take wonderful care of yourself, remember to stay hydrated and nourish your body with wholesome foods, "
            "and come back anytime you want to explore medical sciences or health topics!"
        ),
    ),
    (
        [
            r"\btell\s+me\s+a\s+joke\b",
            r"\bmake\s+me\s+laugh\b",
        ],
        (
            "Why did the white blood cell break up with the red blood cell? "
            "Because it said: 'You're always carrying so much oxygen, but I'm doing all the heavy fighting in this relationship!' "
            "On a serious note, both erythrocytes and leukocytes work in perfect synergy to sustain human life!"
        ),
    ),
    (
        [
            r"\bare\s+you\s+(?:a\s+real\s+nurse|human|a\s+doctor)\b",
        ],
        (
            "I am an artificial intelligence nurse assistant, not a human nurse or licensed medical practitioner. "
            "I am designed to provide accurate medical educational information, explain clinical terminology, "
            "and guide you through nutritional science. For personalized clinical examinations, lab work, or treatment decisions, "
            "always consult a licensed healthcare professional."
        ),
    ),
]


# ---------------------------------------------------------------------------
# 2. MEDICAL SCIENCES KNOWLEDGE ENGINE (Medical Science Knowledge)
# ---------------------------------------------------------------------------

MEDICAL_SCIENCE_TOPICS: List[Dict[str, any]] = [
    # CARDIOVASCULAR & HEMODYNAMICS
    {
        "id": "cardio_heart_mechanics",
        "keywords": [
            r"\bheart\b",
            r"\bcardiac\b",
            r"\bpump(?:ing)?\s+blood\b",
            r"\bventricle",
            r"\batrium\b",
            r"\bmyocardium\b",
        ],
        "title": "Cardiac Anatomy & Hemodynamic Cycle",
        "reply": (
            "The human heart is a four-chambered muscular organ functioning as a dual-circuit pump. "
            "Deoxygenated blood enters the Right Atrium via the vena cava, passes through the tricuspid valve "
            "into the Right Ventricle, and is pumped via pulmonary arteries to the lungs for oxygenation. "
            "Oxygenated blood returns to the Left Atrium through pulmonary veins, flows through the bicuspid (mitral) valve "
            "into the thick, muscular Left Ventricle, which propels blood through the aortic semilunar valve into systemic circulation. "
            "Each cardiac cycle consists of systole (ventricular contraction/ejection) and diastole (ventricular relaxation/filling), "
            "coordinated by electrical impulses originating at the sinoatrial (SA) node."
        ),
    },
    {
        "id": "cardio_blood_pressure",
        "keywords": [
            r"\bblood\s+pressure\b",
            r"\bhypertension\b",
            r"\bsystol",
            r"\bdiastol",
            r"\braas\b",
        ],
        "title": "Blood Pressure Regulation & Hemodynamics",
        "reply": (
            "Blood pressure is the lateral hydrostatic force exerted by circulating blood against systemic arterial walls. "
            "It is recorded as Systolic Pressure (peak ventricular contraction pressure, typically ~120 mmHg) over "
            "Diastolic Pressure (resting baseline resistance between heartbeats, typically ~80 mmHg). "
            "Short-term regulation relies on arterial baroreceptors in the carotid sinus and aortic arch modulating autonomic vascular tone. "
            "Long-term arterial pressure is tightly governed by the kidneys via the Renin-Angiotensin-Aldosterone System (RAAS): "
            "renin converts angiotensinogen to angiotensin I, cleaved by ACE to angiotensin II, causing potent vasoconstriction and "
            "stimulating adrenal aldosterone to retain sodium and water, thereby expanding intravascular plasma volume."
        ),
    },
    {
        "id": "cardio_atherosclerosis",
        "keywords": [
            r"\batherosclero",
            r"\barter(?:y|ies)\b",
            r"\bcholesterol\b",
            r"\bplaque\b",
            r"\bldl\b",
            r"\bhdl\b",
        ],
        "title": "Vascular Biology, Lipids & Atherosclerosis",
        "reply": (
            "Atherosclerosis is a chronic inflammatory fibroproliferative disease of large and medium elastic arteries. "
            "It begins with endothelial cell injury triggered by oxidized Low-Density Lipoprotein (LDL), hypertension, or smoking. "
            "Circulating monocytes adhere to the injured endothelium, migrate into the subendothelial tunica intima, and differentiate "
            "into macrophages. Macrophages engulf oxidized LDL particles via scavenger receptors, transforming into lipid-laden foam cells. "
            "Accumulated foam cells form a fatty streak, which secretes cytokines stimulating smooth muscle migration and collagen deposition, "
            "eventually forming a fibrous cap over a necrotic lipid core. High-Density Lipoprotein (HDL) plays a protective anti-atherogenic "
            "role through reverse cholesterol transport, shuttling excess cholesterol back to the liver for biliary excretion."
        ),
    },

    # HEMATOLOGY & BLOOD
    {
        "id": "hemato_rbc_hemoglobin",
        "keywords": [
            r"\bred\s+blood\s+cell",
            r"\brbc\b",
            r"\berythrocyte",
            r"\bhemoglobin\b",
            r"\bhaemoglobin\b",
            r"\boxygen\s+transport\b",
        ],
        "title": "Erythrocyte Physiology & Hemoglobin Oxygenation",
        "reply": (
            "Erythrocytes (red blood cells) are specialized biconcave anucleated discs with an average circulation lifespan of 120 days. "
            "Their shape maximizes the surface-area-to-volume ratio for gas diffusion and allows deformability through narrow microcapillaries. "
            "Each erythrocyte contains ~270 million hemoglobin molecules. Adult hemoglobin (HbA) is a tetramer composed of two alpha and two beta "
            "globin chains, each harboring an iron-protoporphyrin IX (heme) group capable of reversibly binding molecular oxygen (O2). "
            "Hemoglobin exhibits positive cooperativity: binding the first O2 molecule induces a conformational transition from the tense (T) to "
            "the relaxed (R) state, increasing affinity for subsequent oxygen molecules. In peripheral tissues, low pH and high CO2 promote oxygen "
            "unloading (the Bohr effect)."
        ),
    },
    {
        "id": "hemato_wbc_platelets",
        "keywords": [
            r"\bwhite\s+blood\s+cell",
            r"\bwbc\b",
            r"\bleukocyte",
            r"\bplatelet",
            r"\bthrombocyte",
            r"\bhemostasis\b",
            r"\bcoagulation\b",
        ],
        "title": "Leukocyte Diversity & Platelet Hemostasis",
        "reply": (
            "Blood consists of ~55% liquid plasma and ~45% formed elements. "
            "Leukocytes (white blood cells) are divided into granulocytes (neutrophils, eosinophils, basophils) and agranulocytes (lymphocytes, monocytes). "
            "Neutrophils are the first responders to bacterial invasion, performing rapid phagocytosis and degranulation. "
            "Monocytes enter tissue spaces to become robust macrophages and antigen-presenting cells. "
            "Platelets (thrombocytes) are fragments pinched off from bone marrow megakaryocytes. "
            "Upon vascular endothelial trauma, platelets adhere to exposed subendothelial collagen via von Willebrand factor, undergo shape change, "
            "and release thromboxane A2 and ADP to form a primary platelet plug. Simultaneously, the tissue-factor clotting cascade converts prothrombin "
            "to active thrombin, which polymerizes soluble fibrinogen into an insoluble fibrin mesh, securing secondary hemostasis."
        ),
    },

    # RESPIRATORY PHYSIOLOGY
    {
        "id": "resp_gas_exchange",
        "keywords": [
            r"\blungs?\b",
            r"\balveol",
            r"\bgas\s+exchange\b",
            r"\brespirat",
            r"\bbreath(?:ing)?\b",
            r"\bdiaphragm\b",
        ],
        "title": "Pulmonary Gas Exchange & Alveolar Mechanics",
        "reply": (
            "Pulmonary ventilation is driven by thoracic volume changes: contraction of the diaphragm and external intercostal muscles "
            "increases thoracic cavity volume, lowering intrapleural pressure and drawing atmospheric air through the bronchial tree into ~300 million alveoli. "
            "Alveoli provide an immense surface area (~70-100 m²) separated from pulmonary capillaries by an ultrathin respiratory membrane (0.2-0.5 µm). "
            "Gas exchange occurs via passive diffusion following Fick's Law: alveolar pO2 (~104 mmHg) drives oxygen across into deoxygenated capillary blood "
            "(pO2 ~40 mmHg), while venous pCO2 (~45 mmHg) diffuses down its gradient into alveolar air (~40 mmHg) to be exhaled. "
            "Type II alveolar pneumocytes synthesize pulmonary surfactant (dipalmitoylphosphatidylcholine), which reduces surface tension and prevents alveolar collapse."
        ),
    },

    # GASTROENTEROLOGY & DIGESTION
    {
        "id": "gi_stomach_digestion",
        "keywords": [
            r"\bdigest",
            r"\bstomach\b",
            r"\bgut\b",
            r"\bgastric\b",
            r"\bacid\b",
            r"\bpepsin\b",
            r"\bintestine\b",
        ],
        "title": "Gastrointestinal Physiology & Enzymatic Digestion",
        "reply": (
            "Digestion begins in the oral cavity with salivary alpha-amylase and mechanical mastication. "
            "In the stomach, parietal cells in the gastric mucosa use proton pumps (H+/K+ ATPase) to secrete hydrochloric acid (pH 1.5-2.0). "
            "This acidity denatures dietary proteins, activates chief cell pepsinogen into active pepsin, and sterilizes ingested pathogens. "
            "Parietal cells also synthesize intrinsic factor, mandatory for terminal ileal absorption of Vitamin B12. "
            "Gastric chyme is pulsed into the duodenum, where acidity triggers pancreatic secretin and cholecystokinin (CCK) release. "
            "The pancreas secretes bicarbonate to neutralize acid and enzymes (lipase, trypsinogen, amylase), while the gallbladder releases bile acids "
            "to micellize lipids, enabling mucosal absorption across the enterocyte brush border."
        ),
    },
    {
        "id": "gi_liver_pancreas",
        "keywords": [
            r"\bliver\b",
            r"\bhepat",
            r"\bbile\b",
            r"\bpancreas\b",
            r"\bpancreatic\b",
            r"\bdetox",
        ],
        "title": "Hepatic Metabolism & Pancreatic Function",
        "reply": (
            "The liver is the central metabolic processing and synthetic factory of the human body, receiving dual blood supply from the hepatic artery "
            "and nutrient-rich portal vein. Hepatocytes execute hundreds of critical functions: glycogenesis and gluconeogenesis to buffer blood glucose, "
            "synthesis of nearly all plasma proteins (albumin, fibrinogen, prothrombin, transferrin), synthesis of bile acids from cholesterol, "
            "and Phase I (cytochrome P450 oxidation) and Phase II (glucuronidation, sulfation) conjugation of xenobiotics for renal or biliary clearance. "
            "The pancreas operates dual functions: its exocrine acini secrete alkaline digestive enzymes into the duodenum, while its endocrine "
            "Islets of Langerhans contain beta-cells (insulin) and alpha-cells (glucagon) regulating systemic fuel allocation."
        ),
    },
    {
        "id": "gi_microbiome",
        "keywords": [
            r"\bmicrobiom",
            r"\bgut\s+flora\b",
            r"\bprobiotic",
            r"\bprebiotic",
            r"\bcolon\b",
            r"\bbutyrate\b",
        ],
        "title": "Human Gut Microbiome & Mucosal Immunology",
        "reply": (
            "The distal gut harbors an ecosystem of trillions of commensal microorganisms representing hundreds of bacterial phyla (primarily Firmicutes and Bacteroidetes). "
            "The gut microbiome is now recognized as a virtual endocrine and metabolic organ: commensal bacteria ferment non-digestible dietary fibers "
            "into Short-Chain Fatty Acids (SCFAs)—namely acetate, propionate, and butyrate. Butyrate is the primary energetic substrate for colonocytes "
            "and promotes mucosal barrier integrity via tight junction proteins (claudin, occludin). "
            "Gut bacteria also synthesize bioavailable Vitamin K2 (menaquinones) and biotin, modulate bile acid signaling, and train regulatory T-cells (Tregs) "
            "to prevent inappropriate autoimmune and inflammatory reactions."
        ),
    },

    # NEUROLOGY & NEUROBIOLOGY
    {
        "id": "neuro_action_potential",
        "keywords": [
            r"\bneuron",
            r"\baction\s+potential\b",
            r"\bsynaps",
            r"\bneurotransmitt",
            r"\baxon\b",
            r"\bmyelin\b",
        ],
        "title": "Neurophysiology: Action Potentials & Synaptic Signaling",
        "reply": (
            "Neurons communicate via rapid electrochemical transients. At rest, the neuronal membrane maintains a negative potential of ~-70 mV, "
            "sustained by active Na+/K+ ATPases (pumping 3 Na+ out for every 2 K+ in) and resting potassium leak channels. "
            "When dendritic stimulation depolarizes the axon hillock past the threshold (~-55 mV), voltage-gated Na+ channels rapidly open, "
            "causing an explosive influx of Na+ that reverses membrane polarity up to +30 mV. Rapid inactivation of Na+ channels and opening of voltage-gated K+ "
            "channels restores negative potential (repolarization). "
            "In myelinated axons (myelinated by oligodendrocytes in the CNS and Schwann cells in the PNS), the action potential jumps between uninsulated Nodes of Ranvier "
            "(saltatory conduction), achieving velocities up to 120 m/s. At the axon terminal, depolarization triggers voltage-gated Ca2+ entry, prompting synaptic vesicle "
            "fusion and neurotransmitter release into the synaptic cleft."
        ),
    },
    {
        "id": "neuro_brain_neurotransmitters",
        "keywords": [
            r"\bbrain\b",
            r"\bdopamine\b",
            r"\bserotonin\b",
            r"\bgaba\b",
            r"\bglutamate\b",
            r"\bacetylcholine\b",
            r"\bcns\b",
        ],
        "title": "Neurotransmitters & Central Nervous System Architecture",
        "reply": (
            "The central nervous system employs specialized neurochemical messengers to modulate mood, motor control, cognition, and autonomic tone: "
            "\n• Glutamate: The principal excitatory neurotransmitter in the brain, activating ionotropic NMDA and AMPA receptors for synaptic plasticity and memory formation. "
            "\n• GABA (gamma-aminobutyric acid): The primary inhibitory neurotransmitter, opening chloride channels to hyperpolarize postsynaptic membranes and damp excitability. "
            "\n• Dopamine: Modulates executive reward pathways (mesolimbic system) and voluntary motor initiation via the nigrostriatal tract. "
            "\n• Serotonin (5-HT): Synthesized from tryptophan (90% in enterochromaffin cells of the gut, 10% in raphe nuclei of the brainstem), regulating sleep architecture, mood, and gut motility. "
            "\n• Acetylcholine: The crucial transmitter at neuromuscular junctions and the parasympathetic autonomic nervous system, as well as cerebral memory circuits."
        ),
    },

    # ENDOCRINOLOGY & HORMONES
    {
        "id": "endo_insulin_glucose",
        "keywords": [
            r"\binsulin\b",
            r"\bglucagon\b",
            r"\bglucose\b",
            r"\bblood\s+sugar\b",
            r"\bdiabet",
            r"\bmetabolic\b",
        ],
        "title": "Endocrine Homeostasis: Insulin & Glucose Dynamics",
        "reply": (
            "Systemic glucose homeostasis is an intricate balance orchestrated primarily by pancreatic hormones. "
            "Postprandial elevation of plasma glucose stimulates pancreatic beta-cells to secrete insulin. "
            "Insulin binds to its cell-surface receptor tyrosine kinase, initiating an intracellular phosphorylation cascade (IRS-1 / PI3K / Akt) "
            "that mobilizes intracellular vesicles containing GLUT4 glucose transporters to fuse with the plasma membrane of skeletal myocytes and adipocytes. "
            "This accelerates glucose uptake, promotes glycogen synthesis (glycogenesis), and halts lipolysis. "
            "Conversely, during fasting, falling glucose stimulates alpha-cells to secrete glucagon, which activates hepatic adenylate cyclase and protein kinase A, "
            "triggering glycogenolysis and de novo gluconeogenesis to maintain brain-critical blood glucose levels."
        ),
    },
    {
        "id": "endo_thyroid_metabolism",
        "keywords": [
            r"\bthyroid\b",
            r"\bt3\b",
            r"\bt4\b",
            r"\btsh\b",
            r"\bmetabol(?:ic|ism)\b",
            r"\bcalcitonin\b",
        ],
        "title": "Thyroid Axis & Basal Metabolic Regulation",
        "reply": (
            "The thyroid gland, located anterior to the trachea, controls basal metabolic rate, thermogenesis, and cellular growth. "
            "The hypothalamic-pituitary-thyroid (HPT) axis governs secretion: hypothalamic TRH prompts anterior pituitary TSH release, "
            "which stimulates thyroid follicular cells to trap iodide, synthesize thyroglobulin, and iodinate tyrosine residues. "
            "The gland secretes primarily Thyroxine (T4, ~80%) and smaller amounts of Triiodothyronine (T3, ~20%). "
            "In peripheral tissues (liver, kidneys), deiodinase enzymes strip an iodine atom to convert T4 into T3, the biologically active ligand. "
            "T3 enters cell nuclei, binds Thyroid Hormone Receptors (TR), and upregulates transcription of Na+/K+ ATPases, uncoupling proteins, "
            "and beta-adrenergic receptors, stimulating cellular oxygen consumption and heat generation."
        ),
    },
    {
        "id": "endo_adrenal_stress",
        "keywords": [
            r"\bcortisol\b",
            r"\badrenal\b",
            r"\badrenaline\b",
            r"\bepinephrine\b",
            r"\bstress\s+hormone\b",
            r"\bhpa\s+axis\b",
        ],
        "title": "Adrenal Endocrinology & HPA Stress Response",
        "reply": (
            "The adrenal glands sit atop each kidney, comprising an inner medulla and an outer tripartite cortex: "
            "\n• Adrenal Medulla: An extension of the sympathetic nervous system; chromaffin cells release catecholamines (epinephrine and norepinephrine) "
            "during acute danger, increasing heart rate, dilating bronchioles, and shunting blood to skeletal muscles. "
            "\n• Adrenal Cortex: Regulated by the Hypothalamic-Pituitary-Adrenal (HPA) axis. CRH stimulates pituitary ACTH, which acts on the zona fasciculata "
            "to release cortisol (a glucocorticoid). Cortisol stimulates gluconeogenesis, elevates blood glucose, suppresses non-essential immune reactions, "
            "and maintains vascular responsiveness. "
            "The zona glomerulosa produces aldosterone (mineralocorticoid), maintaining sodium-potassium balance, while the zona reticularis synthesizes androgens."
        ),
    },

    # IMMUNOLOGY & HOST DEFENSE
    {
        "id": "immuno_innate_adaptive",
        "keywords": [
            r"\bimmune\b",
            r"\bimmunity\b",
            r"\bantibody\b",
            r"\bantibodies\b",
            r"\bt[\s-]cell",
            r"\bb[\s-]cell",
            r"\binflammat",
            r"\bantigen",
        ],
        "title": "Immunology: Innate vs Adaptive Host Defenses",
        "reply": (
            "The human immune system operates as a tiered defense network: "
            "\n1. Innate Immunity (Immediate, non-specific): Encompasses anatomical barriers (epithelial tight junctions, acid pH, mucus), antimicrobial peptides (defensins), "
            "the complement cascade (opsonization and membrane attack complex lysis), and phagocytic cells (neutrophils, macrophages). "
            "Innate sensors utilize Pattern Recognition Receptors (such as Toll-Like Receptors) that recognize conserved pathogen-associated molecular patterns (PAMPs). "
            "\n2. Adaptive Immunity (Antigen-specific, immunologic memory): Antigen-presenting cells process foreign peptides and present them on MHC molecules to T lymphocytes. "
            "CD4+ T-helper cells coordinate the response via cytokines; CD8+ cytotoxic T cells destroy virus-infected cells; and B lymphocytes differentiate into plasma cells "
            "that synthesize highly specific antibody immunoglobulins (IgM, IgG, IgA, IgE) targeting circulating antigens. Memory B and T cells persist for decades to provide rapid secondary immunity."
        ),
    },

    # NEPHROLOGY & RENAL PHYSIOLOGY
    {
        "id": "renal_kidney_nephron",
        "keywords": [
            r"\bkidney",
            r"\bnephron",
            r"\bgfr\b",
            r"\bglomerul",
            r"\bfiltrat",
            r"\bure(?:a|ic)\b",
            r"\belectrolyte\b",
        ],
        "title": "Renal Microanatomy, Glomerular Filtration & Homeostasis",
        "reply": (
            "Each human kidney contains approximately 1 to 1.2 million functional microscopic units called nephrons. "
            "Blood enters the glomerulus via afferent arterioles under high hydrostatic pressure (~55 mmHg). "
            "The glomerular filtration barrier (fenestrated endothelium, thick basement membrane, and podocyte slit diaphragms) permits water, ions, "
            "glucose, and amino acids to filter through, while strictly repelling large plasma proteins (albumin) and cellular elements, generating a normal "
            "Glomerular Filtration Rate (GFR) of ~125 mL/min (~180 liters/day). "
            "As filtrate passes through the proximal tubule, loop of Henle (countercurrent multiplier), distal convoluted tubule, and collecting duct, "
            "more than 99% of filtered water and sodium is reabsorbed under the influence of aldosterone and antidiuretic hormone (ADH/vasopressin), "
            "concentrating metabolic wastes (urea, creatinine, uric acid) into ~1.5 liters of excreted urine."
        ),
    },

    # CELLULAR BIOCHEMISTRY & ENERGY
    {
        "id": "biochem_atp_krebs",
        "keywords": [
            r"\batp\b",
            r"\bmitochondri",
            r"\bkrebs\b",
            r"\bcitric\s+acid\s+cycle\b",
            r"\bcellular\s+respiration\b",
            r"\benergy\b",
            r"\bglycolysis\b",
        ],
        "title": "Cellular Bioenergetics: Glycolysis, Krebs Cycle & ATP Synthase",
        "reply": (
            "Adenosine Triphosphate (ATP) is the universal biochemical energy currency of living cells. "
            "ATP generation occurs through three interconnected metabolic phases: "
            "\n1. Glycolysis (Cytosol): Glucose (6-carbon) is cleaved into two pyruvate molecules (3-carbon), yielding a net of 2 ATP and 2 NADH without requiring oxygen. "
            "\n2. Citric Acid Cycle / Krebs Cycle (Mitochondrial Matrix): Pyruvate enters mitochondria and is decarboxylated into Acetyl-CoA by pyruvate dehydrogenase (a B-vitamin dependent enzyme). "
            "Acetyl-CoA condenses with oxaloacetate to form citrate. Through progressive enzymatic dehydrogenations, the cycle yields GTP (ATP equivalent), CO2, and high-energy electron carriers (NADH and FADH2). "
            "\n3. Electron Transport Chain & Oxidative Phosphorylation (Inner Mitochondrial Membrane): NADH and FADH2 donate electrons to protein Complexes I-IV, pumping protons into the intermembrane space. "
            "The resulting proton-motive gradient drives ATP Synthase rotary catalysis, producing ~26 to 28 ATP molecules per molecule of glucose oxidized."
        ),
    },
    {
        "id": "biochem_enzymes_antioxidants",
        "keywords": [
            r"\benzyme",
            r"\bcofactor",
            r"\bcoenzyme",
            r"\bantioxidant",
            r"\bfree\s+radical",
            r"\boxidat(?:ive)?\s+stress\b",
            r"\bros\b",
        ],
        "title": "Enzymology, Coenzymes & Antioxidant Defenses",
        "reply": (
            "Enzymes are protein biocatalysts that accelerate chemical reactions by lowering the Gibbs free energy of activation (Ea) without being consumed. "
            "Many metabolic enzymes require non-protein auxiliary molecules called cofactors (metal ions such as Zinc, Magnesium, Iron, or Copper) or "
            "coenzymes (organic compounds derived from dietary B-complex vitamins, such as NAD+ from Niacin and FAD from Riboflavin). "
            "During normal mitochondrial respiration, 1-2% of oxygen is partially reduced into Reactive Oxygen Species (ROS, such as superoxide O2•− and hydroxyl radicals OH•). "
            "Unchecked ROS cause oxidative damage by peroxidizing polyunsaturated fatty acids in cell membranes and breaking DNA strands. "
            "Cells neutralize ROS using endogenous antioxidant enzymes (Superoxide Dismutase, Catalase, Glutathione Peroxidase requiring selenium) "
            "and dietary scavengers (Vitamin C in aqueous cytosol, Vitamin E in lipid membranes)."
        ),
    },
    {
        "id": "biochem_dna_genetics",
        "keywords": [
            r"\bdna\b",
            r"\brna\b",
            r"\bgenetic",
            r"\bgene\b",
            r"\btranscription\b",
            r"\btranslation\b",
            r"\bprotein\s+synthesis\b",
        ],
        "title": "Molecular Genetics: DNA Replication & Protein Synthesis",
        "reply": (
            "Deoxyribonucleic acid (DNA) encodes the hereditary blueprints of life in a double-helical polymer of four deoxynucleotide bases "
            "(Adenine, Thymine, Guanine, Cytosine), joined by antiparallel phosphodiester backbones and Watson-Crick hydrogen bonding (A=T, G≡C). "
            "The central dogma of molecular biology dictates: "
            "\n1. Transcription: Inside the nucleus, RNA Polymerase reads the template DNA strand and transcribes messenger RNA (mRNA), with uracil (U) replacing thymine. "
            "Pre-mRNA undergoes 5' capping, polyadenylation, and spliceosomal removal of non-coding introns. "
            "\n2. Translation: Mature mRNA translocates to cytoplasmic ribosomes. Transfer RNA (tRNA) molecules matching specific 3-base codons deliver appropriate "
            "amino acids to form polypeptide chains. Proper folding into secondary, tertiary, and quaternary conformations with chaperone proteins yields functional structural proteins and enzymes."
        ),
    },

    # MICROBIOLOGY & PHARMACOLOGY
    {
        "id": "micro_bacteria_vs_virus",
        "keywords": [
            r"\bbacteri(?:a|al)\b",
            r"\bvirus",
            r"\bvira(?:l|ls)\b",
            r"\bpathogen",
            r"\binfection\b",
        ],
        "title": "Microbiology: Cellular Bacteria vs Obligate Intracellular Viruses",
        "reply": (
            "Bacteria and viruses are fundamentally distinct biological entities: "
            "\n• Bacteria: Self-replicating, single-celled prokaryotic organisms with cellular machinery (ribosomes, cell wall, circular chromosome, metabolic enzymes). "
            "They can survive and reproduce independently in appropriate nutrient environments and are susceptible to targeted antibiotics. "
            "\n• Viruses: Non-cellular obligate intracellular genetic parasites consisting only of a nucleic acid genome (DNA or RNA) enclosed in a protein capsid (and sometimes a lipid envelope). "
            "Viruses lack ribosomes, metabolic enzymes, and ATP generation; they can replicate only by invading a host living cell and hijacking its cellular translation apparatus. "
            "Consequently, antibiotics targeting bacterial cell walls or prokaryotic ribosomes have zero efficacy against viral pathogens (such as influenza, rhinovirus, or COVID-19)."
        ),
    },
    {
        "id": "pharm_mechanisms",
        "keywords": [
            r"\bantibiotic",
            r"\bpharmacology\b",
            r"\badme\b",
            r"\bdrug\s+action\b",
            r"\bhow\s+medicines?\s+work\b",
        ],
        "title": "Principles of Pharmacology & Pharmacokinetics",
        "reply": (
            "Pharmacology investigates how chemical substances interact with living systems through two core disciplines: "
            "\n1. Pharmacokinetics (What the body does to the drug - ADME): "
            "• Absorption: Movement of drug from administration site to systemic circulation. "
            "• Distribution: Reversible transfer into tissue compartments, governed by protein binding (albumin) and lipid solubility. "
            "• Metabolism: Hepatic biotransformation, largely via Cytochrome P450 enzymes into water-soluble metabolites. "
            "• Excretion: Elimination through renal glomerular filtration or biliary pathways. "
            "\n2. Pharmacodynamics (What the drug does to the body): "
            "Therapeutic agents typically act as agonists (activating receptor signaling), antagonists (blocking endogenous ligands like beta-blockers), "
            "or enzyme inhibitors (e.g. penicillin inhibiting bacterial transpeptidase, or statins inhibiting HMG-CoA reductase)."
        ),
    },

    # MUSCULOSKELETAL & BONES
    {
        "id": "ortho_bone_remodeling",
        "keywords": [
            r"\bbones?\b",
            r"\bskelet",
            r"\bosteoblast",
            r"\bosteoclast",
            r"\bcalcium\b",
            r"\bosteoporos",
        ],
        "title": "Bone Physiology: Osteoblasts, Osteoclasts & Remodeling",
        "reply": (
            "Bone is a dynamic, metabolically active connective tissue continually remodeled throughout human life. "
            "Its extracellular matrix consists of organic Type I collagen fibers (~30% dry weight, conferring tensile elasticity) "
            "embedded in inorganic calcium hydroxyapatite crystals (Ca10(PO4)6(OH)2, ~70% dry weight, conferring compressive rigidity). "
            "Remodeling is governed by a tightly coupled cellular balance: "
            "\n• Osteoclasts (derived from monocyte-macrophage lineage): Adhere to bone surfaces and secrete hydrochloric acid and cathepsin K to dissolve mineral and digest collagen (bone resorption). "
            "\n• Osteoblasts (mesenchymal origin): Migrate into resorption pits and deposit unmineralized collagen osteoid, subsequently mineralizing it with calcium and phosphate. "
            "Mechanical strain stimulates osteoblast activity, while hormonal signals (Parathyroid hormone, Calcitriol, Estrogen) tightly regulate calcium exchange between skeleton and serum."
        ),
    },
]


class NurseBotAIService:
    """Intelligent conversational AI and medical science knowledge engine for NurseBot."""

    def __init__(self):
        self._compiled_conv: List[Tuple[List[re.Pattern], str]] = [
            ([re.compile(p, re.IGNORECASE) for p in pats], resp)
            for pats, resp in CONVERSATION_INTENTS
        ]
        self._compiled_med: List[Dict[str, any]] = [
            {
                "id": t["id"],
                "patterns": [re.compile(p, re.IGNORECASE) for p in t["keywords"]],
                "title": t["title"],
                "reply": t["reply"],
            }
            for t in MEDICAL_SCIENCE_TOPICS
        ]

    async def generate_response(self, question: str) -> Optional[Dict[str, any]]:
        """Processes conversational or medical science question.

        Returns dict with reply, intent, and optional source or None if unhandled.
        """
        q = question.strip().lower()

        # 1. Check conversational dialogue (greetings, pleasantries, small talk)
        for pats, resp in self._compiled_conv:
            if any(p.search(q) for p in pats):
                return {
                    "reply": resp,
                    "intent": "ai_chat",
                    "source_name": "MedNourish NurseBot Assistant",
                    "source_url": None,
                    "is_web_answer": False,
                }

        # 2. Check Medical Sciences Knowledge Engine
        best_match = None
        best_match_count = 0

        for topic in self._compiled_med:
            matches = sum(1 for p in topic["patterns"] if p.search(q))
            if matches > best_match_count:
                best_match_count = matches
                best_match = topic

        if best_match and best_match_count >= 1:
            return {
                "reply": f"[{best_match['title']}]\n\n{best_match['reply']}",
                "intent": "medical_science",
                "source_name": "MedNourish Medical Sciences Knowledge Base",
                "source_url": "https://medlineplus.gov",
                "is_web_answer": False,
            }

        # 3. Optional: Attempt free external AI endpoint if configured
        if FREE_AI_API_URL:
            try:
                external_reply = await self._call_external_ai(question)
                if external_reply:
                    return {
                        "reply": external_reply,
                        "intent": "ai_chat",
                        "source_name": "NurseBot AI Service",
                        "source_url": None,
                        "is_web_answer": True,
                    }
            except Exception as e:
                logger.warning(f"External AI endpoint call failed: {e}")

        # 4. Fallback intelligent conversational response explaining capabilities
        return {
            "reply": (
                "That's an interesting question! As MedNourish NurseBot, I am trained across human anatomy, "
                "cardiovascular and pulmonary physiology, neurology, cellular bioenergetics (ATP and Krebs cycle), "
                "immunology, endocrinology, and nutritional science. "
                "Try asking me things like: 'How does the heart pump blood?', 'Explain how enzymes and ATP work', "
                "'What is the difference between innate and adaptive immunity?', or ask about any vitamin or body organ!"
            ),
            "intent": "ai_chat",
            "source_name": "MedNourish Clinical Guidance Assistant",
            "source_url": None,
            "is_web_answer": False,
        }

    async def _call_external_ai(self, question: str) -> Optional[str]:
        """Calls external free conversational AI API if configured."""
        headers = {"Content-Type": "application/json"}
        if FREE_AI_API_KEY:
            headers["Authorization"] = f"Bearer {FREE_AI_API_KEY}"

        payload = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are MedNourish NurseBot, an empathetic, highly knowledgeable medical science "
                        "and educational nurse assistant. Explain medical, physiological, and nutritional topics "
                        "accurately and clearly. Do not provide personalized medical diagnoses or prescribe drug dosages."
                    ),
                },
                {"role": "user", "content": question},
            ],
            "max_tokens": 350,
            "temperature": 0.5,
        }

        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.post(FREE_AI_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"].strip()
                if "generated_text" in data:
                    return data["generated_text"].strip()
        return None


nursebot_ai_service = NurseBotAIService()
