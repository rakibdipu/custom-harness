"""
Knowledge Vault - Verified, High-Retention Content Database
Contains rigorously structured, psychologically grounded scripts with real experiments,
historical case studies, and high-conversion hooks.
No generic AI slop. Pure high-retention value.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ─── PSYCHOLOGY & MINDSET (MindEdge) ──────────────────────────────────────────
# Formatted for 45-55s vertical video (130-155 words).
# Structure: Hook (0-3s) -> The Study/Experiment -> The Subconscious Mechanism -> The Countermeasure/Power Move -> Retention Loop

PSYCHOLOGY_VAULT = [
    {
        "id": "ai_friend_trap",
        "topic": "What Happens When AI Becomes Your Friend?",
        "title": "What Happens When AI Becomes Your Friend?",
        "title_card": "THE AI FRIEND TRAP",
        "hook": "What if the person you talk to most isn't even human?",
        "study": "In 2026, millions of people are turning to AI companions for emotional support. And on the surface, it feels completely safe.",
        "mechanism": "There is zero awkward silence, no fear of judgment, and instant validation. But human relationships are built on reciprocity, repair, and healthy friction. When you replace real connection with an agreeable algorithm, your subconscious slowly loses the tolerance for human messiness.",
        "action": "Don't confuse effortless availability with genuine intimacy.",
        "loop": "Follow MindEdge for your daily mental edge.",
        "tags": ["psychology", "mentalhealth", "ai", "relationships", "mindset", "mindedge"],
        "broll_keywords": ["young adult dark bedroom glowing phone", "smartphone screen glowing neural interface", "glowing ai companion split real friends cafe", "silhouette looking out window night", "person walking outside warm sunlight"]
    },
    {
        "id": "ai_zero_risk",
        "topic": "Why Talking to AI Feels So Easy",
        "title": "Why Talking to AI Feels So Easy",
        "title_card": "ZERO SOCIAL RISK",
        "hook": "Ever noticed why it's easier to tell AI your deepest secrets than to call your closest friend?",
        "study": "When you text a real person, your brain calculates social risk: will they judge you, leave you on read, or change how they see you?",
        "mechanism": "AI removes that entire evolutionary threat with instant responsiveness, infinite patience, and zero vulnerability hangover. But comfort is not connection. Removing social friction also removes the exact struggle that makes deep trust possible.",
        "action": "Stop using synthetic safety to avoid real conversations.",
        "loop": "Follow MindEdge for your daily mental edge.",
        "tags": ["socialskills", "communication", "psychologyfacts", "overthinking", "mindset", "mindedge"],
        "broll_keywords": ["person holding smartphone hesitating call", "fingers typing fast ai chat glowing screen", "neural brain pathways lighting up glowing gold", "two people distant bench street lamp dusk", "young person talking face to face sunlight"]
    },
    {
        "id": "ai_loneliness_paradox",
        "topic": "Could AI Make You More Lonely?",
        "title": "Could AI Make You More Lonely?",
        "title_card": "LONELINESS PARADOX",
        "hook": "Can talking to an AI actually cure your loneliness, or does it make it worse?",
        "study": "Recent psychological research reveals a surprising dual reality. For isolated individuals, chatting with an AI companion can provide immediate emotional relief and lower short-term distress.",
        "mechanism": "But when used as a permanent substitute for human presence, it creates an artificial comfort zone. It trains your brain to expect conversations where you are never challenged, never misunderstood, and always agreed with.",
        "action": "AI is a life raft, not the destination. Use technology for clarity, but seek humans for connection.",
        "loop": "Follow MindEdge for your daily mental edge.",
        "tags": ["loneliness", "psychology", "aiethics", "connection", "mentalhealth", "mindedge"],
        "broll_keywords": ["person sitting alone modern glass apartment night", "holographic geometric glowing figure phone", "eyes reflecting glowing algorithmic waveforms", "person walking crowded evening street market", "two hands handshake warm golden light"]
    },
    {
        "id": "pratfall_effect",
        "topic": "The Pratfall Effect: Why Flaws Make You Magnetic",
        "title": "Why Spilling Your Coffee Makes People Like You More",
        "title_card": "THE PRATFALL EFFECT",
        "hook": "If you want someone to instantly like you, stop trying to look flawless.",
        "study": "In 1966, social psychologist Elliot Aronson ran a famous experiment at the University of Minnesota. He had contestants answer 50 difficult trivia questions, then accidentally spill coffee all over their clothes. The results shocked everyone.",
        "mechanism": "When an exceptionally competent person makes a minor, clumsy blunder, their perceived likability skyrockets by nearly 40%. It breaks the subconscious barrier of intimidation and makes you human.",
        "action": "The secret? Competence must come first. Be undeniably skilled at what you do, but never hide your quirks. Perfection breeds resentment; controlled vulnerability commands loyalty.",
        "loop": "Have you ever liked someone more after seeing them make an awkward mistake? Drop your thoughts below.",
        "tags": ["psychology", "socialskills", "influence", "mindset", "pratfalleffect"],
        "broll_keywords": ["coffee spill", "man in suit thinking", "chess board", "intense eye contact", "crowd smiling"]
    },
    {
        "id": "ben_franklin_effect",
        "topic": "The Benjamin Franklin Effect: How to Turn Enemies Into Allies",
        "title": "The Dirty Psychological Trick to Make Anyone Like You",
        "title_card": "BEN FRANKLIN EFFECT",
        "hook": "You don't win people over by doing them favors. You do it by getting them to do a favor for you.",
        "study": "In 1737, Benjamin Franklin faced a bitter political rival in the Pennsylvania assembly who refused to speak with him. Instead of kissing up to him or arguing, Franklin asked to borrow a rare book from his personal library.",
        "mechanism": "When the rival agreed, his subconscious suffered severe cognitive dissonance. The human brain cannot justify doing a favor for someone it hates, so it rewires its belief: 'I must actually like him.'",
        "action": "Next time you need to win over an enemy or a cold colleague, don't buy them lunch. Ask them for small advice, borrow a pen, or ask for their expert opinion. Their own ego will do the rest.",
        "loop": "Would you ever lend a favor to someone you disliked? Try this tomorrow and watch what happens.",
        "tags": ["persuasion", "darkpsychology", "benfranklin", "influence", "socialhacks"],
        "broll_keywords": ["antique book library", "two men negotiation", "strategic silence", "chess move", "man thinking"]
    },
    {
        "id": "spotlight_effect",
        "topic": "The Spotlight Effect: Curing Social Anxiety Instantly",
        "title": "Nobody Is Looking at You (The Spotlight Effect)",
        "title_card": "THE SPOTLIGHT EFFECT",
        "hook": "Here is a harsh reality that will instantly cure your social anxiety: nobody is thinking about you.",
        "study": "In 2000, researchers at Cornell University forced students to wear an embarrassing Barry Manilow t-shirt into a crowded room. The wearers estimated that at least 50% of the room noticed. In reality, less than 20% even looked.",
        "mechanism": "Psychologists call this the Spotlight Effect. Because we live inside our own heads, we falsely believe a bright spotlight is tracking our every mistake, our outfit, and our awkward pauses.",
        "action": "Everyone around you is trapped in their own mental mirror, obsessing over their own flaws. When you realize everyone is self-conscious, you stop seeking permission and start moving with quiet authority.",
        "loop": "What is one thing you held back from doing because you feared being judged? It's time to let it go.",
        "tags": ["confidence", "socialanxiety", "spotlighteffect", "mentalmodels", "freedom"],
        "broll_keywords": ["crowd walking city", "silhouette looking at mirror", "neon street rain", "dramatic spotlight", "confident walk"]
    },
    {
        "id": "zeigarnik_effect",
        "topic": "The Zeigarnik Effect: How Your Brain Gets Addicted",
        "title": "Why Your Brain Obsesses Over Unfinished Business",
        "title_card": "THE ZEIGARNIK EFFECT",
        "hook": "Why do you stay awake at 3 AM obsessing over that one unanswered text?",
        "study": "In the 1920s, psychologist Bluma Zeigarnik sat in a bustling Vienna café and noticed something bizarre. The waiters remembered complex unpaid orders with 100% accuracy, but the second the bill was paid, the order was completely erased from their memory.",
        "mechanism": "Your subconscious mind opens a high-priority cognitive loop whenever a task or conversation is left unresolved. It generates background anxiety that refuses to shut down until closure is reached.",
        "action": "This is why top storytellers use cliffhangers and elite negotiators never give away the ending early. If you want someone to think about you all day, leave the last sentence unsaid.",
        "loop": "Do you still think about something from years ago that never got closure? Tell me in the comments.",
        "tags": ["darkpsychology", "zeigarnik", "brainhacks", "memory", "humanbehavior"],
        "broll_keywords": ["clock ticking midnight", "phone glowing in dark", "cafe waiter vintage", "spinning hourglass", "thoughtful face"]
    },
    {
        "id": "asch_conformity",
        "topic": "The Asch Experiment: How Groups Force You to Lie",
        "title": "75% of People Will Deny Their Own Eyes to Fit In",
        "title_card": "THE ASCH EXPERIMENT",
        "hook": "If everyone in a room looked at a red wall and swore it was blue, would you disagree?",
        "study": "In 1951, Solomon Asch placed one real participant in a room with 7 actors. They were shown lines of obviously different lengths. One by one, every actor chose the clearly wrong line.",
        "mechanism": "Over 75% of normal, intelligent people caved and chose the wrong answer at least once. The brain prioritizes social belonging over objective reality because historically, being cast out of the tribe meant physical death.",
        "action": "The masses don't follow truth; they follow consensus. The moment you understand this, you stop seeking validation from crowds that are simply conforming to each other's fears.",
        "loop": "Would you stand alone against the room, or would you doubt your own eyes? Be honest below.",
        "tags": ["conformity", "psychology", "independence", "deepthoughts", "truth"],
        "broll_keywords": ["group of people standing", "lone figure walking opposite", "black and white crowd", "shadow silhouette", "intense eyes"]
    },
    {
        "id": "strategic_silence",
        "topic": "The 4-Second Rule: The Power of Strategic Silence",
        "title": "Why Master Negotiators Stay Silent for 4 Seconds",
        "title_card": "THE 4-SECOND RULE",
        "hook": "The most dangerous weapon in any negotiation is not what you say. It is the silence after you stop talking.",
        "study": "FBI hostage negotiator Chris Voss revealed that human beings have an involuntary psychological panic response to dead silence. In North American and European cultures, an unfilled pause longer than 3.5 seconds creates intense social pressure.",
        "mechanism": "Amateurs rush to fill silence because discomfort makes them feel powerless. Master communicators do the opposite: they make a statement, lock eyes, and wait. The other party will inevitably reveal their real boundary just to kill the awkwardness.",
        "action": "Next time someone gives you an unfair offer or insults you, do not react. Count to 4 in your head while looking directly between their eyebrows. Watch them negotiate against themselves.",
        "loop": "Can you hold silence without feeling awkward? Try this in your next conversation.",
        "tags": ["negotiation", "chrisvoss", "bodylanguage", "strategicsilence", "power"],
        "broll_keywords": ["two people boardroom table", "calm face dark lighting", "hourglass sand trickling", "chess king falling", "man drinking water calm"]
    },
    {
        "id": "door_in_the_face",
        "topic": "Door-in-the-Face Technique: The Anchor Trick",
        "title": "How Manipulators Make You Agree to Anything",
        "title_card": "THE ANCHOR TRAP",
        "hook": "How do you get someone to agree to a 20-dollar favor? Ask them for a hundred first.",
        "study": "Psychologist Robert Cialdini tested this by asking college students to chaperone juvenile delinquents on a day trip to the zoo. 83% said no. But when he first asked them to volunteer 2 hours a week for 2 full years, and THEN asked for the zoo trip, compliance tripled.",
        "mechanism": "This is the Door-in-the-Face technique. When someone rejects your massive initial demand, their brain feels guilty. The second you offer a smaller compromise, they perceive it as a concession and feel obligated to say yes.",
        "action": "Always know what you actually want before entering a negotiation. Pitch the outrageous request first, let them slam the door, and then gracefully present your true target.",
        "loop": "Has anyone ever used this tactic on you without you noticing? Save this so you never fall for it.",
        "tags": ["cialdini", "influence", "persuasion", "negotiationskills", "psychology"],
        "broll_keywords": ["closed door dark corridor", "handshake deal", "luxury pen signing", "man counting money", "confident smirk"]
    },
    {
        "id": "pygmalion_effect",
        "topic": "The Pygmalion Effect: The Science of High Expectations",
        "title": "How Other People's Thoughts Secretly Program Your Brain",
        "title_card": "THE PYGMALION EFFECT",
        "hook": "What people believe about your intelligence can alter your actual IQ score.",
        "study": "In 1968, Harvard researcher Robert Rosenthal told elementary school teachers that a special test had identified 20% of their students as 'intellectual bloomers' who would soon experience massive cognitive leaps. In reality, the names were chosen completely at random from a hat.",
        "mechanism": "By the end of the year, those exact random students showed massive, measurable increases in objective IQ tests. The teachers had unconsciously given them warmer eye contact, more challenging questions, and deeper encouragement.",
        "action": "You perform to the level of the expectations placed upon you by your closest circle. If your friends treat you like average, you will subconsciously cap your own potential. Audit your environment ruthlessly.",
        "loop": "Who in your life pushes your expectations higher? Tag them or leave a follow.",
        "tags": ["pygmalioneffect", "mindset", "success", "psychology", "growth"],
        "broll_keywords": ["classroom chalkboard", "student reading book", "man looking out skyscraper", "sunrise golden light", "stairs climbing up"]
    }
]

# ─── STORYTELLING & LIFE LESSONS (StoryVault) ─────────────────────────────────
# Formatted for gripping, suspenseful, historical/parable narration with high emotion.

STORY_VAULT = [
    {
        "id": "roman_general_silence",
        "topic": "The Roman General Who Defeated an Army Without a Weapon",
        "title": "The Weapon That Defeated 50,000 Men Without Bloodshed",
        "title_card": "THE ART OF RESTRAINT",
        "hook": "In 217 BC, Rome faced annihilation by Hannibal, the greatest military genius in history.",
        "story": "Every Roman general who marched out was slaughtered within hours. In desperation, the Senate appointed Fabius as supreme dictator. But Fabius did something that made Romans call him a coward.",
        "twist": "He refused to fight. He shadowed Hannibal from the hills, cutting off food supplies and burning crops, while retreating whenever provoked.",
        "moral": "By starving Hannibal's war machine without losing his soldiers, Fabius broke Carthage and saved Rome. Real strength is having the discipline to outlast your enemy's ego.",
        "loop": "Do you have the patience to play the long game? Tell me below.",
        "tags": ["history", "stoicism", "wisdom", "discipline", "strategy"],
        "broll_keywords": ["roman soldier armor", "foggy battlefield hills", "ancient map candlelight", "solitary warrior silhouette", "burning torch night"]
    },
    {
        "id": "kintsugi_gold",
        "topic": "The Japanese Philosophy of Kintsugi: Beauty in Brokenness",
        "title": "Why the Japanese Repair Broken Bowls With 24K Gold",
        "title_card": "KINTSUGI WISDOM",
        "hook": "In 15th-century Japan, a military commander accidentally shattered his favorite tea bowl into pieces.",
        "story": "Instead of throwing it away, Japanese craftsmen rejoined the fragments with lacquer mixed with pure 24-karat gold. The cracks were not hidden; they were highlighted.",
        "twist": "The repaired bowl became infinitely more valuable than the original. This ancient practice is called Kintsugi: the art of golden repair.",
        "moral": "People often hide their heartbreaks and failures in shame. But Japanese wisdom teaches that the places where you were broken and rebuilt are the most sacred parts of your story.",
        "loop": "What breakdown in your past made you stronger? Never hide your gold.",
        "tags": ["kintsugi", "japanesewisdom", "resilience", "philosophy", "healing"],
        "broll_keywords": ["ceramic bowl breaking", "gold liquid pouring", "japanese zen garden", "artisan hands working", "warm glowing lamp"]
    },
    {
        "id": "chinese_farmer_maybe",
        "topic": "The Parable of the Taoist Farmer: The Myth of Good and Bad Luck",
        "title": "The 2,000-Year-Old Parable That Ends All Overthinking",
        "title_card": "THE PARABLE OF MAYBE",
        "hook": "An ancient Chinese farmer lived in a mountain village with only one horse to plow his fields.",
        "story": "One day, his horse ran away. The neighbors cried: 'What terrible luck!' The farmer replied: 'Maybe.' Next morning, the horse returned, leading seven wild stallions. 'What great luck!' they shouted. 'Maybe,' he said.",
        "twist": "Next day, his son broke both legs trying to tame a stallion. 'What a tragedy!' they wept. 'Maybe,' said the farmer. Two days later, the army arrived to draft all young men for war. His son was spared.",
        "moral": "You never know if a setback is a disaster or a blessing in disguise. Never judge your life until the full story unfolds.",
        "loop": "Has a past failure ever turned into your greatest blessing? Think about it.",
        "tags": ["taoism", "mindset", "ancientwisdom", "parable", "peaceofmind"],
        "broll_keywords": ["wild horses running misty meadow", "ancient mountain village", "old wise man looking valley", "soldier marching dust", "calm sunset river"]
    },
    {
        "id": "two_wolves_inside",
        "topic": "The Cherokee Legend of the Two Wolves",
        "title": "The Constant War Inside Your Head Right Now",
        "title_card": "WHICH WOLF WINS?",
        "hook": "An old Cherokee grandfather sat by a campfire, teaching his grandson about the human heart.",
        "story": "He said: 'A terrible battle is raging inside everyone. It is a war between two fierce wolves. One wolf is envy, anger, self-doubt, and greed. The other wolf is courage, discipline, kindness, and truth.'",
        "twist": "The young boy looked into the flames, frightened by the war within him, and asked: 'Grandfather, which wolf wins?'",
        "moral": "The elder smiled gently: 'The one you feed.' Every second you spend doomscrolling, indulging jealousy, or giving into weakness feeds the dark wolf. Choose your habits wisely.",
        "loop": "Which wolf did you feed today with your choices? Share below.",
        "tags": ["cherokee", "legend", "selfmastery", "discipline", "wisdom"],
        "broll_keywords": ["wolf eyes glowing dark", "crackling campfire night", "old tribal elder silhouette", "mountain pines fog", "starry night sky"]
    }
]

# ─── RELATABLE COMEDY & TRUTHS (TooReal Facts) ────────────────────────────────
# Dry wit, relatable modern observations, sharp comedic timing for US Millennials/Gen-Z.

COMIC_VAULT = [
    {
        "id": "alarm_snooze_math",
        "topic": "The Delusion of 5-Minute Alarm Snooze Math",
        "title": "The Absolute Delusion of Morning Alarm Math",
        "title_card": "ALARM SNOOZE MATH",
        "hook": "Why does setting an alarm for 6:00 AM feel like a death sentence, but 6:09 AM feels like luxury?",
        "script": [
            "We all have that internal negotiator at 6 AM who genuinely believes that 7 extra minutes of trash sleep will cure twenty years of exhaustion.",
            "You set four alarms: 6:00, 6:05, 6:08, and 6:12, as if your subconscious is calculating compound interest on sleep debt.",
            "Then you wake up at 6:45 in sheer panic, brush your teeth with your eyes closed, and swear you'll sleep early tonight... only to end up watching penguin documentaries at 2 AM."
        ],
        "punchline": "Adulting is just making promises to your future self that you have zero intention of keeping.",
        "loop": "How many alarms do you have set right now? Be honest below.",
        "tags": ["relatable", "morningstruggle", "sleepmath", "comedy", "funnyreels"],
        "broll_keywords": ["smartphone alarm glowing 6am", "person covered blanket dark", "coffee brewing steam", "panicked morning run", "clock digital glowing"]
    },
    {
        "id": "quick_call_scam",
        "topic": "The Corporate Horror of 'Do You Have a Quick Second?'",
        "title": "The Biggest Lie in Modern Corporate History",
        "title_card": "QUICK CALL LIES",
        "hook": "The phrase 'Hey, do you have a quick two minutes?' is the corporate equivalent of a hostage situation.",
        "script": [
            "The notification pops up on Slack and your heart drops, because 'two minutes' has never, in human history, meant two minutes.",
            "It instantly turns into a 45-minute monologue where someone screenshares a spreadsheet with ninety tabs that have nothing to do with your job.",
            "You just sit there nodding like a broken bobblehead, saying 'makes total sense', while mentally calculating how much money you need to fake your death and buy a goat farm."
        ],
        "punchline": "If someone asks for a quick second, close your laptop and run for your life.",
        "loop": "Who at your job does this every single day? Hit like if you feel the pain.",
        "tags": ["workhumor", "corporatelife", "relatable", "officememes", "slacktrauma"],
        "broll_keywords": ["slack notification screen", "exhausted office worker face", "empty conference room", "laptop slamming shut", "coffee mug cold"]
    },
    {
        "id": "grocery_cart_rich",
        "topic": "The Psychological Stages of Entering a Grocery Store",
        "title": "Why You Walk Out of the Store With Everything Except Milk",
        "title_card": "GROCERY STORE DELUSION",
        "hook": "Going into a grocery store for two specific items is the ultimate test of willpower, and we fail every time.",
        "script": [
            "You walk through the automatic sliding doors with pure confidence: 'I just need eggs and bread.' You refuse a cart to stay honest.",
            "Five minutes later, you are waddling down aisle seven holding four fancy cheeses, three bags of chips, and an imported hot sauce that will sit in your fridge until 2035.",
            "You get to the register with your arms overflowing with random luxury snacks, and realize you completely forgot the eggs."
        ],
        "punchline": "Grocery stores aren't stores; they are psychological traps designed to rob your wallet with snacks.",
        "loop": "What is the weirdest impulse buy in your pantry right now? Drop it below.",
        "tags": ["groceryshopping", "impulsebuy", "relatable", "funny", "memes"],
        "broll_keywords": ["supermarket shopping cart", "aisle shelves snacks", "credit card tap payment", "man holding too many items", "laughing exhausted face"]
    },
    {
        "id": "leaving_party_irish_exit",
        "topic": "The High Art of the Irish Exit",
        "title": "Why Saying Goodbye at a Party Takes 45 Minutes",
        "title_card": "THE IRISH EXIT",
        "hook": "Saying goodbye to a group of friends is a 45-minute diplomatic summit that nobody wants to attend.",
        "script": [
            "You announce you're leaving, and suddenly four people scream 'No, stay!' Someone hands you tap water, and another starts telling a story about their cousin's dog.",
            "You end up standing near the front door in your winter coat for 35 minutes, sweating profusely, having the exact same conversation with three different people.",
            "This is why the Irish Exit is an act of tactical survival: slide through the kitchen, slip out the back door, and vanish into the night like Batman."
        ],
        "punchline": "Ghosting a party isn't selfish; it's respecting everyone's precious time.",
        "loop": "Are you a 45-minute goodbye person or an Irish Exit master? Tell me below.",
        "tags": ["sociallife", "irishexit", "introvertproblems", "relatable", "funny"],
        "broll_keywords": ["crowded house party silhouettes", "man walking out front door night", "coat zipper closing", "empty night street quiet", "relief smile car"]
    }
]

# ─── FUN EDUCATIONAL CARTOON (CartoonBrain) ──────────────────────────────────
CARTOON_VAULT = [
    {
        "id": "brain_vs_sugar",
        "topic": "What Sugar Does to Your Brain in 10 Seconds",
        "title": "What Happens in Your Brain When You Eat Sugar 🍩",
        "title_card": "SUGAR BRAIN RUSH",
        "hook": "The exact second sugar touches your tongue, your brain triggers a massive fireworks show!",
        "scenes": [
            {"scene": 1, "heading": "The Sugar Alarm", "script": "Your taste receptors fire high-speed emergency signals straight to your cerebral cortex like a laser light show."},
            {"scene": 2, "heading": "The Dopamine Flood", "script": "Your brain's reward center releases a massive tidal wave of dopamine, identical to what happens in video game addiction."},
            {"scene": 3, "heading": "The Crash Monster", "script": "Thirty minutes later, your blood glucose plunges and the grumpy tired monster inside your head takes complete control!"}
        ],
        "punchline": "Next time you crave cookies, remember your brain is just an easily tricked supercomputer.",
        "loop": "What sweet snack are you secretly addicted to? Comment below!",
        "tags": ["cartoon", "funfacts", "educational", "scienceanimation", "brain"],
        "broll_keywords": ["cartoon brain thinking colorful", "sugar crystals glowing", "happy cartoon character eating", "tired sleepy face cartoon"]
    },
    {
        "id": "sleep_brain_wash",
        "topic": "The Nightly Janitors Cleaning Your Brain While You Sleep",
        "title": "Your Brain Literally Washes Itself Every Night 🧠✨",
        "title_card": "NIGHTLY BRAIN WASH",
        "hook": "Did you know that while you are dreaming, your brain literally shrinks and takes a bath?",
        "scenes": [
            {"scene": 1, "heading": "The Janitors Clock In", "script": "The moment you enter deep slow-wave sleep, your brain cells physically shrink by sixty percent to make room."},
            {"scene": 2, "heading": "The Power Wash", "script": "Cerebrospinal fluid rushes through your synapses like a power washer, scrubbing away toxic waste proteins that cause memory fog."},
            {"scene": 3, "heading": "The Morning Reset", "script": "Skip sleep, and those toxic trash bags stay piled up in your mental living room all day long!"}
        ],
        "punchline": "Sleep isn't laziness; it's high-tech biological maintenance.",
        "loop": "How many hours of sleep did you get last night? Be honest in the comments!",
        "tags": ["cartoon", "sleepscience", "funanimation", "brainfacts", "didyouknow"],
        "broll_keywords": ["sleeping cartoon character cozy", "sparkling clean bubbles animation", "clock midnight glowing", "happy refreshed character morning"]
    }
]

# ─── DEEP DIVE LONG FORM (MindEdge Long) ──────────────────────────────────────
LONG_VIDEO_VAULT = [
    {
        "id": "deep_dopamine_detox",
        "topic": "The Complete Neuroscience of Dopamine Detox",
        "title": "The 21-Day Neuroscience Reset to Reclaim Your Focus and Dopamine",
        "title_card": "DOPAMINE NEUROSCIENCE",
        "hook": "In 1954, neuroscientists James Olds and Peter Milner made an accidental discovery that explains why you cannot put down your phone.",
        "intro": "Every action you take, every goal you chase, and every habit that controls you is governed by a single neurochemical: dopamine. Today, we break down the exact biological protocol to rewire your reward system in 21 days.",
        "chapters": [
            {"number": 1, "title": "The Accidental Discovery of the Reward Circuit", "script": "In their McGill University laboratory, Olds and Milner implanted electrodes into the brains of rats, intending to test the reticular formation. Instead, they accidentally stimulated the septal area. When given a lever to stimulate this region, the rats pressed it up to seven thousand times per hour, choosing stimulation over food, water, and sleep until total collapse."},
            {"number": 2, "title": "The Pleasure-Pain Balance", "script": "Dr. Anna Lembke, professor of psychiatry at Stanford, revealed that dopamine functions on an opposing pleasure-pain balance. Whenever you experience an artificial dopamine spike from cheap short-form video or junk food, your brain compensates by tilting the scale into a deficit, creating anxiety and restlessness."},
            {"number": 3, "title": "Receptor Downregulation and Tolerance", "script": "When flooded with excessive stimulation, your post-synaptic neurons defend themselves by pulling dopamine D2 receptors inside the cell membrane. This downregulation means things that once brought you joy—reading, deep conversations, creative work—now feel dreadfully boring."},
            {"number": 4, "title": "The 21-Day Reset Protocol", "script": "Scientific evidence demonstrates that it takes approximately three weeks for neural receptors to upregulate back to baseline sensitivity. Week one requires eliminating high-stimulus friction triggers. Week two introduces deliberate boredom. Week three reconstructs effort-based dopamine pathways."},
            {"number": 5, "title": "Sustained Mental Mastery", "script": "When you master your dopamine, you reclaim the rarest superpower of the modern age: deep, uninterrupted, effortless focus."}
        ],
        "outro": "If you are ready to take control of your mind, subscribe to MindEdge. Leave a comment with what bad habit you plan to eliminate first.",
        "tags": ["dopaminedetox", "neuroscience", "focus", "productivity", "mindset"],
        "broll_keywords": ["vintage laboratory microscope", "human brain glowing neural network", "man reading book deeply focused", "calm ocean horizon sunrise", "silhouette climbing mountain peak"]
    }
]


STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "with",
    "by", "from", "of", "about", "why", "how", "what", "who", "whom", "this",
    "that", "these", "those", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "you", "your", "yours", "we",
    "our", "ours", "they", "their", "them", "people", "more", "most", "all",
    "some", "any", "no", "not", "only", "own", "same", "so", "than", "too",
    "very", "can", "will", "just", "should", "now", "make", "makes", "get", "gets",
    "need", "stop", "over"
}


def _clean_title(topic: str, prefix: str = "") -> str:
    """Format a clean, viral title from topic string"""
    t = topic.strip()
    words = t.split()
    capitalized = " ".join(w.capitalize() if w.lower() not in STOPWORDS else w.lower() for w in words)
    capitalized = capitalized[0].upper() + capitalized[1:] if capitalized else ""
    if prefix and not any(capitalized.lower().startswith(p) for p in ["why ", "how ", "3 ", "5 ", "the "]):
        res = f"{prefix} {capitalized}"
    else:
        res = capitalized
    return res[:70]


class KnowledgeVault:
    """Provides high-retention, verified scripts with procedural fallback for any topic"""

    def __init__(self):
        self.psychology = list(PSYCHOLOGY_VAULT)
        self.story = list(STORY_VAULT)
        self.comic = list(COMIC_VAULT)
        self.cartoon = list(CARTOON_VAULT)
        self.long_video = list(LONG_VIDEO_VAULT)
        self.used_vault_ids: set[str] = set()

        # Dynamically load all 90 TooReal Facts scripts if available
        try:
            tooreal_file = Path(__file__).parent.parent / "accounts" / "tooreal_90_plan.json"
            if tooreal_file.exists():
                with open(tooreal_file, "r", encoding="utf-8") as f:
                    plan_json = json.load(f)
                    for day_data in plan_json.get("days", []):
                        for v in day_data.get("videos", []):
                            h_raw = v.get("hook", "")
                            p = v.get("punchline", "")
                            cb = v.get("comment_bait", "Tell me in the comments if this is you.")
                            t = v.get("title", "")
                            v_id = v.get("id", "")
                            
                            h_clean = h_raw.strip()
                            if not any(pw in h_clean.lower() for pw in ["truth", "why", "never", "nobody", "actually", "real", "bizarre", "everyone", "exact", "nothing"]):
                                hook = f"Here is the bizarre truth: {h_clean}"
                            else:
                                hook = h_clean
                                
                            sec1 = "You start out genuinely convinced you have total control over the situation, but five seconds in, reality decides to humble your entire existence."
                            sec2 = "Your brain starts frantically calculating forty-seven disastrous possibilities while you just stand there nodding into the void."
                            sec3 = f"{p}"
                            cta = f"Follow TooReal Facts for your daily dose of sanity, and tell me in the comments: {cb}"
                            
                            self.comic.append({
                                "id": f"tooreal_{v_id.lower()}",
                                "topic": t,
                                "title": t,
                                "title_card": t[:25].upper(),
                                "hook": hook,
                                "script": [sec1, sec2],
                                "punchline": sec3,
                                "loop": cta,
                                "tags": ["relatable", "memes", "comedy", "funny", "tooreal", "humor", "fyp"],
                                "broll_keywords": [
                                    f"{t} comic pop art",
                                    "exaggerated cartoon funny shocked expression pop art",
                                    "chaotic comic pop art neon green action lines",
                                    "comic pop art exhausted character vertical 9:16"
                                ]
                            })
        except Exception as e:
            logger.warning(f"Could not load tooreal_90_plan into KnowledgeVault: {e}")



    def _find_vault_match(self, items: list, topic: Optional[str]) -> Optional[Dict[str, Any]]:
        """Strict matching against curated vault items using non-stopword keywords"""
        if not topic:
            return None
        import re
        topic_words = set(re.findall(r"\b[a-z]{3,}\b", topic.lower())) - STOPWORDS
        if not topic_words:
            return None

        for item in items:
            if item.get("id") in self.used_vault_ids:
                continue
            id_words = set(item.get("id", "").split("_")) - STOPWORDS
            title_words = set(re.findall(r"\b[a-z]{3,}\b", item.get("title", "").lower())) - STOPWORDS
            # Require at least 2 distinct non-stopword keyword matches
            if len(topic_words & id_words) >= 2 or len(topic_words & title_words) >= 2:
                self.used_vault_ids.add(item["id"])
                return item
        return None

    def get_psychology_script(self, topic: Optional[str] = None, channel_name: str = "MindEdge") -> Dict[str, Any]:
        """Fetch matching psychology script or dynamically generate a custom script for this topic"""
        match = self._find_vault_match(self.psychology, topic)

        if match:
            voiceover = (
                f"{match['hook']} "
                f"{match['study']} "
                f"{match['mechanism']} "
                f"{match['action']} "
                f"{match['loop']}"
            )
            return {
                "title": match["title"],
                "title_card": match["title_card"],
                "hook": match["hook"],
                "sections": [
                    {"heading": "The Experiment", "script": match["study"]},
                    {"heading": "The Mechanism", "script": match["mechanism"]},
                    {"heading": "The Power Move", "script": match["action"]}
                ],
                "cta": match["loop"],
                "voiceover": voiceover,
                "broll_keywords": match["broll_keywords"],
                "image_prompts": [
                    f"{k}, dark cinematic lighting, 9:16 vertical, photorealistic, 4k"
                    for k in match["broll_keywords"][:4]
                ],
                "description": f"{match['title']}\n\n{match['hook']}\n\nUnderstanding this psychological principle gives you an unfair advantage in social dynamics and personal mastery.\n\nSubscribe/Follow for daily mental insights.",
                "hashtags": " ".join([f"#{t}" for t in match["tags"]]),
                "tags": match["tags"]
            }

        # Dynamic procedural script tailored to the exact topic
        topic_text = (topic or "the psychology of daily mastery").strip()
        title = _clean_title(topic_text, "The Brutal Truth About")
        hook = f"Stop scrolling. Here is the brutal truth about {topic_text.lower()} that 99% of people realize way too late."
        s1 = "Most people stay trapped in identical cycles because the human mind defaults to comfortable excuses rather than confronting uncomfortable realities."
        s2 = f"When you decode {topic_text.lower()}, your subconscious pattern shifts from passive reaction to deliberate emotional control."
        s3 = "High-performing individuals never rely on temporary motivation. They enforce quiet discipline, set uncompromising boundaries, and execute without hesitation."
        cta = f"Follow {channel_name} for daily psychological insights that give you an unfair advantage. Drop your thoughts below."
        voiceover = f"{hook} {s1} {s2} {s3} {cta}"

        return {
            "title": title,
            "title_card": "THE BRUTAL TRUTH",
            "hook": hook,
            "sections": [
                {"heading": "The Subconscious Trap", "script": s1},
                {"heading": "The Cognitive Shift", "script": s2},
                {"heading": "The Power Move", "script": s3}
            ],
            "cta": cta,
            "voiceover": voiceover,
            "broll_keywords": [topic_text, "dark cinematic lighting portrait", "intense focused eyes shadow", "chess king victory concept"],
            "image_prompts": [
                f"{topic_text}, dark cinematic lighting, 9:16 vertical, dramatic atmosphere",
                "dramatic silhouette face in shadow, anamorphic lens, 4k",
                "chess king standing alone dark board, dramatic lighting",
                "lone figure walking city street rain neon, mysterious aesthetic"
            ],
            "description": f"{title}\n\nUnderstanding this psychological principle gives you an unfair advantage.\n\nFollow for daily mental insights.",
            "hashtags": "#psychology #mindset #motivation #success #mentalmodels",
            "tags": ["psychology", "mindset", "selfimprovement"]
        }

    def get_story_script(self, topic: Optional[str] = None, channel_name: str = "StoryVault") -> Dict[str, Any]:
        """Fetch matching story or dynamically generate an engaging narrative for this topic"""
        match = self._find_vault_match(self.story, topic)

        if match:
            voiceover = (
                f"{match['hook']} "
                f"{match['story']} "
                f"{match['twist']} "
                f"{match['moral']} "
                f"{match['loop']}"
            )
            return {
                "title": match["title"],
                "title_card": match["title_card"],
                "hook": match["hook"],
                "sections": [
                    {"heading": "The Legend", "script": match["story"]},
                    {"heading": "The Turning Point", "script": match["twist"]},
                    {"heading": "The Wisdom", "script": match["moral"]}
                ],
                "cta": match["loop"],
                "voiceover": voiceover,
                "broll_keywords": match["broll_keywords"],
                "image_prompts": [
                    f"{k}, cinematic emotional warm light, dramatic atmosphere, 9:16 vertical"
                    for k in match["broll_keywords"][:4]
                ],
                "description": f"{match['title']}\n\n{match['moral']}\n\nA timeless story on character, discipline, and emotional strength.\n\nFollow for daily life lessons.",
                "hashtags": " ".join([f"#{t}" for t in match["tags"]]),
                "tags": match["tags"]
            }

        # Dynamic procedural storytelling script tailored to the exact topic
        topic_text = (topic or "the power of unseen resilience").strip()
        title = _clean_title(topic_text, "The Untold Story:")
        hook = f"History remembers the loud, but civilizations were built by moments like {topic_text.lower()} that almost nobody talks about."
        s1 = "In an era driven by chaos and insurmountable odds, a single resolve proved that human character is forged in the silent battles nobody witnesses."
        s2 = "When every ally surrendered and defeat seemed guaranteed, one unshakeable decision shattered the conventional rules and rewrote the entire outcome."
        s3 = "True strength is never about brute force. It is the quiet endurance to hold your ground until the storms pass and victory emerges."
        cta = f"Follow {channel_name} for timeless life lessons and historical wisdom. Share this with someone who needs strength today."
        voiceover = f"{hook} {s1} {s2} {s3} {cta}"

        return {
            "title": title,
            "title_card": "THE UNTOLD STORY",
            "hook": hook,
            "sections": [
                {"heading": "The Trial", "script": s1},
                {"heading": "The Turning Point", "script": s2},
                {"heading": "The Moral", "script": s3}
            ],
            "cta": cta,
            "voiceover": voiceover,
            "broll_keywords": [topic_text, "ancient dramatic landscape", "lone warrior looking valley", "sunrise calm river cinematic"],
            "image_prompts": [
                f"{topic_text}, cinematic emotional warm light, 9:16 vertical",
                "ancient epic landscape golden hour clouds",
                "lone silhouette on cliff overlooking stormy ocean",
                "historic portrait thoughtful expression vintage oil painting"
            ],
            "description": f"{title}\n\nA timeless story of courage and resilience.\n\nFollow for daily life lessons.",
            "hashtags": "#story #motivation #history #lifelessons #wisdom",
            "tags": ["story", "motivation", "history", "wisdom"]
        }

    def get_comic_script(self, topic: Optional[str] = None, channel_name: str = "TooReal Facts") -> Dict[str, Any]:
        """Fetch matching comic script or dynamically generate hilarious relatable bits for this topic"""
        match = self._find_vault_match(self.comic, topic)

        if match:
            script_text = " ".join(match["script"])
            voiceover = f"{match['hook']} {script_text} {match['punchline']} {match['loop']}"
            return {
                "title": match["title"],
                "title_card": match["title_card"],
                "hook": match["hook"],
                "sections": [
                    {"heading": "The Setup", "script": match["script"][0]},
                    {"heading": "The Chaos", "script": match["script"][1]},
                    {"heading": "The Reality", "script": match["punchline"]}
                ],
                "cta": match["loop"],
                "voiceover": voiceover,
                "broll_keywords": match["broll_keywords"],
                "image_prompts": [
                    f"{k}, modern vibrant cinematic lighting, relatable comedy aesthetic, 9:16"
                    for k in match["broll_keywords"][:4]
                ],
                "description": f"{match['title']}\n\n{match['hook']}\n\nToo real because reality is the funniest show on earth.\n\nFollow for your daily dose of sanity.",
                "hashtags": " ".join([f"#{t}" for t in match["tags"]]),
                "tags": match["tags"]
            }

        # Dynamic procedural comedy script tailored to the exact topic
        topic_text = (topic or "the universal struggle of daily life").strip()
        title = _clean_title(topic_text, "The Honest Reality of")
        hook = f"Nobody warns you about the sheer everyday trauma of {topic_text.lower()}, but we all live through it."
        b1 = "You convince yourself you have total control over the situation until reality decides to humble your entire existence in five seconds flat."
        b2 = "Then your brain starts calculating forty-seven disastrous possibilities while you just stand there nodding like an overwhelmed bobblehead."
        b3 = "At this point, simply surviving the day without embarrassing yourself in public is considered an absolute Olympic-level achievement."
        cta = f"Follow {channel_name} for your daily dose of sanity, and tell me in the comments if you relate to this."
        voiceover = f"{hook} {b1} {b2} {b3} {cta}"

        return {
            "title": title,
            "title_card": "TOO REAL TO IGNORE",
            "hook": hook,
            "sections": [
                {"heading": "The Setup", "script": b1},
                {"heading": "The Spiral", "script": b2},
                {"heading": "The Reality", "script": b3}
            ],
            "cta": cta,
            "voiceover": voiceover,
            "broll_keywords": [topic_text, "exhausted funny face office", "person looking at smartphone shocked", "running away chaotic meme"],
            "image_prompts": [
                f"{topic_text}, comic pop art bold colors, vibrant dramatic lighting",
                "funny relatable expression exhausted face, comic pop art style",
                "person holding head in hands laughing meme aesthetic",
                "dramatic funny neon background 9:16 vertical"
            ],
            "description": f"{title}\n\n{hook}\n\nFollow for more hilarious relatable truths.",
            "hashtags": "#funny #relatable #comedy #viral #memes",
            "tags": ["funny", "relatable", "comedy", "viral"]
        }

    def get_cartoon_script(self, topic: Optional[str] = None, channel_name: str = "CartoonBrain") -> Dict[str, Any]:
        """Fetch matching cartoon script or dynamically generate fun educational scenes for this topic"""
        match = self._find_vault_match(self.cartoon, topic)

        if match:
            scene_scripts = " ".join([s["script"] for s in match["scenes"]])
            voiceover = f"{match['hook']} {scene_scripts} {match['punchline']} {match['loop']}"
            return {
                "title": match["title"],
                "title_card": match["title_card"],
                "hook": match["hook"],
                "scenes": match["scenes"],
                "sections": [
                    {"heading": s["heading"], "script": s["script"]}
                    for s in match["scenes"]
                ],
                "cta": match["loop"],
                "punchline": match["punchline"],
                "voiceover": voiceover,
                "broll_keywords": match["broll_keywords"],
                "image_prompts": [
                    f"{k}, cartoon anime vibrant colorful aesthetic, 9:16 vertical"
                    for k in match["broll_keywords"][:4]
                ],
                "description": f"{match['title']}\n\n{match['hook']}\n\nFun science facts made simple and entertaining!\n\nFollow {channel_name} for daily fun facts!",
                "hashtags": " ".join([f"#{t}" for t in match["tags"]]),
                "tags": match["tags"]
            }

        topic_text = (topic or "how things actually work").strip()
        title = _clean_title(topic_text, "Crazy Science:")
        hook = f"Wait, did you know that the science behind {topic_text.lower()} is way crazier than you ever imagined?"
        sc1 = "Imagine your brain running like a supercomputer that suddenly decides to open forty browser tabs all at once."
        sc2 = "Tiny chemical messengers sprint across trillions of connections at 200 miles per hour just to keep your body functioning."
        punch = "Next time you feel tired, remember your body is literally performing billions of micro-miracles every single second!"
        cta = f"Follow {channel_name} for fun daily science adventures, and tell me what crazy fact we should explore next!"
        voiceover = f"{hook} {sc1} {sc2} {punch} {cta}"

        return {
            "title": title,
            "title_card": "MIND-BLOWING SCIENCE",
            "hook": hook,
            "sections": [
                {"heading": "The Brain Tab Explosion", "script": sc1},
                {"heading": "The Chemical Sprint", "script": sc2},
                {"heading": "The Everyday Miracle", "script": punch}
            ],
            "cta": cta,
            "punchline": punch,
            "voiceover": voiceover,
            "broll_keywords": [topic_text, "cartoon brain glowing colorful", "cute cartoon character running fast", "sparkling science laboratory anime"],
            "image_prompts": [
                f"{topic_text}, colorful cartoon anime style, vibrant 9:16",
                "cute animated character looking shocked, Studio Ghibli quality",
                "colorful neural network glowing cartoon sparkles",
                "bright cheerful scientific background with fun animations"
            ],
            "description": f"{title}\n\nFun educational cartoon facts made simple!\n\nFollow {channel_name} for daily fun!",
            "hashtags": "#cartoon #science #funfacts #education #animation",
            "tags": ["cartoon", "funny", "educational"]
        }

    def get_long_video_script(
        self,
        topic: Optional[str] = None,
        channel_name: str = "MindEdge",
        account_id: str = ""
    ) -> Dict[str, Any]:
        """
        Generate a full 6-chapter episodic long-form video (5-7 minutes)
        specifically tailored to the host persona and visual style of the channel.
        """
        # Determine channel type
        c_lower = channel_name.lower()
        is_comic = (account_id == "comic_viral") or ("tooreal" in c_lower) or ("comic" in c_lower)
        is_story = (account_id == "storytelling") or ("story" in c_lower)
        
        topic_text = (topic or "the hidden truth behind human nature").strip()

        if is_comic:
            return self._build_comic_long_video(topic_text, channel_name)
        elif is_story:
            return self._build_story_long_video(topic_text, channel_name)
        else:
            return self._build_psychology_long_video(topic_text, channel_name)

    def _build_psychology_long_video(self, topic: str, channel_name: str) -> Dict[str, Any]:
        """Dr. Julian Vance — Dark Academia / Neuroscience Deep Dive (6 Chapters)"""
        title = _clean_title(topic, "The Dark Psychology of")
        clean_name = topic.lower()

        chapters = [
            {
                "number": 1,
                "name": "The Silent Cognitive Trap",
                "title": "The Silent Cognitive Trap",
                "voiceover": (
                    f"Consider for a moment how easily human perception is manipulated when {clean_name} enters our daily lives. "
                    "Every day, millions of people operate under the dangerous illusion that their thoughts and decisions are entirely their own. "
                    "Yet beneath the surface of conscious awareness, subtle behavioral triggers and cognitive vulnerabilities quietly dictate our choices. "
                    "When we encounter this psychological friction, our prefrontal cortex automatically defaults to convenient mental shortcuts. "
                    "If you have ever felt inexplicable hesitation or an irrational surge of overthinking, you have already stood directly inside this psychological crosshair."
                ),
                "broll_prompts": [
                    "Dr Julian Vance neuropsychologist in vintage dark academia library, 35mm film grain, warm amber keylight",
                    "glowing human brain cortex neural synapse firing, cinematic macro lighting",
                    "antique ticking stopwatch on mahogany desk, dramatic shadows, warm studio atmosphere",
                    "intense close-up of human eyes reflecting glowing computer screen in darkness"
                ]
            },
            {
                "number": 2,
                "name": "The Evolutionary Origin",
                "title": "The Evolutionary Origin",
                "voiceover": (
                    f"To truly understand why {clean_name} exerts such a visceral hold over our minds, we must look two hundred thousand years into our evolutionary past. "
                    "In early hunter-gatherer societies, social ostracization or making a miscalculated social gamble meant literal biological death. "
                    "Our ancestors survived because their primitive nervous systems developed hyper-sensitive threat-detection radars. "
                    "Today, that exact ancient survival mechanism is completely misfiring in the modern world. "
                    "Your brain cannot distinguish between a real predator in the jungle and the artificial anxieties produced by modern social pressure."
                ),
                "broll_prompts": [
                    "primitive human silhouettes around glowing ancient campfire, misty wilderness night",
                    "ancient cave paintings lit by torchlight, flickering golden glow, dramatic shadows",
                    "evolutionary skull transformation sequence, cinematic museum exhibit lighting",
                    "lone silhouette walking through dense foggy pine forest, atmospheric cold mist"
                ]
            },
            {
                "number": 3,
                "name": "The Neurochemical Hijack",
                "title": "The Neurochemical Hijack",
                "voiceover": (
                    f"Neurologically speaking, when {clean_name} takes hold of your mental state, an intense chemical chain reaction detonates within milliseconds. "
                    "Your amygdala triggers a micro-surge of cortisol and norepinephrine, rapidly tightening your perceptual field and elevating mental friction. "
                    "Simultaneously, post-synaptic dopamine receptors temporarily downregulate, leaving you feeling restless, depleted, and vulnerable to external influence. "
                    "Brain scans consistently reveal that during these cognitive hijack states, rational problem-solving regions essentially go offline. "
                    "Understanding this biological reality is the single most important prerequisite to regaining your emotional sovereignty."
                ),
                "broll_prompts": [
                    "microscopic 3D rendering of neurotransmitters flooding neural synapse, vibrant amber and deep blue",
                    "fMRI brain scan visualization with glowing prefrontal cortex activity, high-tech dark lab",
                    "flowing liquids inside vintage chemical glassware, dramatic laboratory rim light",
                    "abstract glowing neural network expanding in dark space, 4k ultra detailed"
                ]
            },
            {
                "number": 4,
                "name": "Manipulation in the Wild",
                "title": "Manipulation in the Wild",
                "voiceover": (
                    f"Now observe how {clean_name} is actively weaponized against you in modern society. "
                    "From targeted corporate marketing and viral algorithmic hooks to covert social manipulators, this vulnerability is deliberately exploited. "
                    "Skilled manipulators understand that keeping you in an unsettled emotional state makes you significantly more agreeable and compliant. "
                    "They utilize manufactured scarcity, strategic silences, and calculated micro-criticisms to keep your self-worth off balance. "
                    "Once you train your mind to spot these subtle patterns in real time, the manipulator's power over your thoughts completely evaporates."
                ),
                "broll_prompts": [
                    "glass skyscraper corporate boardroom silhouette overlooking sprawling rainy city at night",
                    "glowing smartphone screen illuminating exhausted face in pitch black room",
                    "wooden chessboard with falling black king piece, slow motion, dramatic backlighting",
                    "two shadowy figures in intense quiet conversation, cinematic film noir lighting"
                ]
            },
            {
                "number": 5,
                "name": "The Cognitive Armor Protocol",
                "title": "The Cognitive Armor Protocol",
                "voiceover": (
                    f"To neutralize the insidious effects of {clean_name}, you must implement a rigorous 3-step psychological defense protocol. "
                    "First: The Tactical Pause. When the stimulus hits, introduce an intentional four-second breath before offering any response or decision. "
                    "Second: Emotional Disidentification. Mentally label the sensation as biological data rather than your absolute identity. "
                    "Third: Reality Decoupling. Ask yourself whether your emotional reaction serves your highest long-term objective or merely an insecure reflex. "
                    "Practicing these three steps systematically rewires your neuro-pathways from reactive victim to deliberate commander."
                ),
                "broll_prompts": [
                    "man sitting in leather armchair writing deliberate notes in a leather journal, amber desk lamp",
                    "hourglass with golden sand steadily falling through glass waist, high detail macro shot",
                    "ancient marble statue of Stoic philosopher Marcus Aurelius, soft chiaroscuro lighting",
                    "focused warrior tightening leather armor straps, cinematic dramatic resolve"
                ]
            },
            {
                "number": 6,
                "name": "Architect of Your Reality",
                "title": "Architect of Your Reality",
                "voiceover": (
                    f"Mastering {clean_name} is not merely about defense; it is about becoming the undisputed architect of your mental kingdom. "
                    "Those who cannot control their emotional responses will forever remain pawns in the schemes of those who can. "
                    "True intellectual strength is never loud or combative; it is quiet, unshakeable, and completely self-contained. "
                    f"If this analytical deep dive brought clarity to your thinking, subscribe to {channel_name} and join our community of disciplined minds. "
                    "Drop a comment sharing which psychological insight resonated with you most today, and remember: master your mind, or someone else will."
                ),
                "broll_prompts": [
                    "Dr Julian Vance closing antique leather book in dark academia study, looking directly into lens",
                    "lone figure standing atop majestic mountain peak watching golden sunrise break through clouds",
                    "sunbeams cutting through dusty cathedral window, cinematic atmospheric rays",
                    "calm ocean waves gently meeting rocky shoreline at dawn, tranquil and powerful"
                ]
            }
        ]

        for ch in chapters:
            ch["script"] = ch["voiceover"]

        full_voiceover = " ".join([ch["voiceover"] for ch in chapters])
        hook_text = f"The hidden dangerous truth about {clean_name} is that most people never realize how easily their perception is manipulated."
        top_image_prompts = [p for ch in chapters for p in ch.get("broll_prompts", [])][:6]
        return {
            "title": f"{title} | Full Documentary",
            "title_card": "DARK PSYCHOLOGY",
            "hook": hook_text,
            "intro": chapters[0]["voiceover"],
            "chapters": chapters,
            "sections": [{"heading": ch["name"], "script": ch["voiceover"]} for ch in chapters],
            "outro": chapters[-1]["voiceover"],
            "cta": f"Subscribe to {channel_name} for daily psychological mastery.",
            "voiceover": full_voiceover,
            "image_prompts": top_image_prompts,
            "thumbnail_prompt": f"Dramatic dark academia study, glowing brain synapse, bold text {title[:30]}",
            "broll_keywords": [
                f"{topic} dark academia",
                "human brain glowing neuroscience",
                "chessboard falling king piece dramatic",
                "hourglass sand flowing warm lighting",
                "man mountain sunrise cinematic"
            ],
            "description": (
                f"{title}\n\n"
                f"An analytical deep dive into the psychological roots and covert mechanisms of {topic}.\n\n"
                "Timestamps:\n" +
                "\n".join([f"0{i}:00 - {ch['name']}" for i, ch in enumerate(chapters, 1)]) +
                f"\n\nSubscribe to {channel_name} for more evidence-based psychological strategies."
            ),
            "hashtags": "#psychology #darkpsychology #neuroscience #mindset #selfmastery #stoicism",
            "tags": ["psychology", "dark psychology", "neuroscience", "mindset", "stoicism", "human behavior"]
        }

    def _build_story_long_video(self, topic: str, channel_name: str) -> Dict[str, Any]:
        """Captain Marcus Kane — Epic Historical Saga & Life Lesson (6 Chapters)"""
        title = _clean_title(topic, "The Legend of")
        clean_name = topic.lower()

        chapters = [
            {
                "number": 1,
                "name": "Prologue: The Shadow of Destiny",
                "title": "Prologue: The Shadow of Destiny",
                "voiceover": (
                    f"History has a quiet way of hiding its most extraordinary souls, until the tale of {clean_name} demands to be told. "
                    "Long before the history books turned their ink to gold, ordinary individuals faced trials that seemed designed to crush the human heart. "
                    "In an era where survival required unbending discipline, our story begins on a forgotten frontier where hope was considered a dangerous luxury. "
                    "The winds carried whispers of an impending storm, yet none could have foreseen the colossal crucible that was about to unfold. "
                    "Light your pipe, draw close to the lantern, and listen to a chronicle of courage that refuses to die."
                ),
                "broll_prompts": [
                    "Captain Marcus Kane weathered sea captain in 19th-century naval cabin, flickering lantern light, sepia oil painting style",
                    "ancient sailing vessel battling towering ocean waves in midnight storm, cinematic vintage texture",
                    "antique leather-bound journal opening with brass lock, quill pen and parchment",
                    "flickering candle flame illuminating old hand-drawn nautical map on wooden table"
                ]
            },
            {
                "number": 2,
                "name": "Act I: The Gathering Tempest",
                "title": "Act I: The Gathering Tempest",
                "voiceover": (
                    f"When the crisis of {clean_name} first broke, it did not arrive with fanfare, but with the suddenness of an avalanche. "
                    "Every reliable resource was instantly severed, leaving a handful of weary souls stranded against insurmountable odds. "
                    "Rations grew thin as winter closed its icy grip, and the horizon offered nothing but barren expanse and merciless silence. "
                    "Where weaker spirits collapsed in despair, a solitary figure stood tall, surveying the devastation with unflinching resolve. "
                    "They knew that survival was no longer a question of strength, but a test of sheer psychological defiance."
                ),
                "broll_prompts": [
                    "lone explorer walking through fierce arctic blizzard, frostbitten face, fur coat, vintage sepia tone",
                    "historical fortress battlements in heavy dark fog, ancient stone walls, dramatic torches",
                    "distressed crew huddling around small iron stove inside creaking wooden cabin",
                    "dramatic lightning flash illuminating stormy mountain ridge, dark dramatic historical mood"
                ]
            },
            {
                "number": 3,
                "name": "Act II: The Brink of Ruin",
                "title": "Act II: The Brink of Ruin",
                "voiceover": (
                    f"Days bled into grueling weeks, pushing the struggle of {clean_name} to its absolute breaking point. "
                    "One by one, every calculated lifeline collapsed beneath unforeseen betrayals and unforgiving terrain. "
                    "Hunger gnawed at their bones, sleep was stolen by fever, and the shadows of doubt whispered that continuing the march was madness. "
                    "In those midnight hours, when darkness felt eternal, the boundary between mortal endurance and legend was forged. "
                    "To surrender would have been easy; to take even a single step forward required an act of supernatural defiance."
                ),
                "broll_prompts": [
                    "close-up of weathered hands gripping worn wooden oars through freezing sea spray",
                    "shadowy historical campfire with smoke rising into starry night sky, melancholic mood",
                    "worn leather boots trudging through mud and snow, historical expedition aesthetic",
                    "exhausted silhouette looking out over vast empty desert dunes at twilight"
                ]
            },
            {
                "number": 4,
                "name": "Act III: The Audacious Gambit",
                "title": "Act III: The Audacious Gambit",
                "voiceover": (
                    f"When all conventional strategy failed, the decisive turning point of {clean_name} was born of sheer tactical audacity. "
                    "Refusing the inevitable trap of retreat, they devised a bold maneuver that defied every established rule of engagement. "
                    "Under cover of midnight fog, the plan was executed with breathtaking stealth and razor-sharp timing. "
                    "The adversaries, lulled into arrogant security, never anticipated that an enemy so bruised could strike with such surgical precision. "
                    "In one daring stroke, the entire balance of destiny was seized and violently rewritten."
                ),
                "broll_prompts": [
                    "tactical historical war map with wooden figurines and brass compass, candlelight glow",
                    "stealth silhouettes slipping through misty riverbank at midnight, historical warfare",
                    "determined captain gripping ship helm amidst breaking storm, water crashing on deck",
                    "intense close-up of determined eyes reflecting golden torchlight in the dark"
                ]
            },
            {
                "number": 5,
                "name": "Act IV: The Breaking of Dawn",
                "title": "Act IV: The Breaking of Dawn",
                "voiceover": (
                    f"When the smoke finally parted and the morning sun broke across the horizon, the saga of {clean_name} stood revealed. "
                    "Against every mathematical probability and expert prediction, the impossible line had been held and conquered. "
                    "Scars were etched deep into both flesh and memory, but their spirits remained unbroken and untamed. "
                    "The surrounding world watched in stunned disbelief as those who had been written off as doomed stepped forward victorious. "
                    "They had not merely survived the tempest; they had conquered their own mortal limitations."
                ),
                "broll_prompts": [
                    "majestic wooden ship sailing into calm golden harbor at sunrise, historic oil painting aesthetic",
                    "exhausted victorious survivors embracing on sunlit clifftop overlooking calm sea",
                    "golden morning sunbeams breaking through parting dark storm clouds over fortress",
                    "ancient stone bell tower ringing out celebration across historic coastal city"
                ]
            },
            {
                "number": 6,
                "name": "Epilogue: The Echo Across Eternity",
                "title": "Epilogue: The Echo Across Eternity",
                "voiceover": (
                    f"Centuries may pass, but the timeless truth embedded within {clean_name} remains an eternal compass for our own lives. "
                    "Whenever you face your own impossible storm, remember that history was never made by those who sought comfort or surrendered to despair. "
                    "The same indomitable fire that sustained these legends lives quietly within your own chest today. "
                    f"If these forgotten chronicles inspire your journey, subscribe to {channel_name} and help us preserve history's greatest untold sagas. "
                    "Leave a comment with what chapter moved you most, and until our next voyage, keep your lantern burning bright."
                ),
                "broll_prompts": [
                    "Captain Marcus Kane raising antique brass cup in warm candlelit cabin, looking at viewer with respect",
                    "old brass compass resting on worn nautical chart next to glowing pipe smoke, sepia tones",
                    "timeless lighthouse beam sweeping over calm night ocean beneath starry sky",
                    "leather-bound book closing gently, ancient dust motes dancing in warm sunbeam"
                ]
            }
        ]

        for ch in chapters:
            ch["script"] = ch["voiceover"]

        full_voiceover = " ".join([ch["voiceover"] for ch in chapters])
        hook_text = f"The real untold truth of {clean_name} was hidden from history for decades, until now."
        top_image_prompts = [p for ch in chapters for p in ch.get("broll_prompts", [])][:6]
        return {
            "title": f"{title} | The Epic Historical Chronicle",
            "title_card": "EPIC CHRONICLES",
            "hook": hook_text,
            "intro": chapters[0]["voiceover"],
            "chapters": chapters,
            "sections": [{"heading": ch["name"], "script": ch["voiceover"]} for ch in chapters],
            "outro": chapters[-1]["voiceover"],
            "cta": f"Subscribe to {channel_name} for history's greatest stories.",
            "voiceover": full_voiceover,
            "image_prompts": top_image_prompts,
            "thumbnail_prompt": f"Vintage historic ship storm, flickering lantern, bold text {title[:30]}",
            "broll_keywords": [
                f"{topic} vintage retro history",
                "sailing ship stormy seas oil painting",
                "explorer wilderness blizzard vintage",
                "brass compass candlelight nautical map",
                "lighthouse beam starry ocean night"
            ],
            "description": (
                f"{title}\n\n"
                f"The gripping historical saga and timeless life lessons of {topic}.\n\n"
                "Chapters:\n" +
                "\n".join([f"0{i}:00 - {ch['name']}" for i, ch in enumerate(chapters, 1)]) +
                f"\n\nSubscribe to {channel_name} for more epic chronicles and forgotten wisdom."
            ),
            "hashtags": "#history #storytelling #epicstories #motivation #lifelessons #resilience",
            "tags": ["history", "storytelling", "epic story", "resilience", "motivation", "life lessons"]
        }

    def _build_comic_long_video(self, topic: str, channel_name: str) -> Dict[str, Any]:
        """Alex Miller — Satirical Pop-Art Relatable Comedy Special (6 Chapters)"""
        title = _clean_title(topic, "The Absolute Disaster of")
        clean_name = topic.lower()

        chapters = [
            {
                "number": 1,
                "name": "Part 1: The Innocent Delusion",
                "title": "Part 1: The Innocent Delusion",
                "voiceover": (
                    f"Let us sit down and conduct a serious forensic investigation into the daily catastrophe known as {clean_name}. "
                    "Every single day, perfectly sane adult human beings convince themselves: 'Today will be different. Today I have a system.' "
                    "You wake up with the naive confidence of a Silicon Valley CEO who just had their first green smoothie. "
                    "You tell yourself that you are going to handle this situation with absolute grace, efficiency, and maturity. "
                    "Little do you know, the universe has already scheduled a hilarious ambush to humble your entire existence in three minutes flat."
                ),
                "broll_prompts": [
                    "Alex Miller comic host wearing modern streetwear and backwards cap, comic pop art style, bold outlines, vibrant colors",
                    "comic illustration of confident person sipping iced coffee with thumbs up, bright yellow background, pop art",
                    "smartphone alarm showing 6am with glowing comic speech bubbles, Roy Lichtenstein aesthetic",
                    "bold comic halftone background with vibrant explosion patterns and neon colors"
                ]
            },
            {
                "number": 2,
                "name": "Part 2: The Illusion of Total Control",
                "title": "Part 2: The Illusion of Total Control",
                "voiceover": (
                    f"Now observe Stage Two of the {clean_name} experience: the phase of fraudulent overconfidence. "
                    "This is where you start doing complex mental gymnastics to justify your terrible decisions. "
                    "You invent brand new mathematical formulas that violate all known laws of physics just to convince yourself you have plenty of time. "
                    "You tell yourself: 'I will just check this for thirty seconds,' which is the most widely documented lie in modern human civilization. "
                    "Deep down, you know the train is already completely off the tracks, but you continue smiling like everything is completely fine."
                ),
                "broll_prompts": [
                    "comic character staring at complex mathematical whiteboard formulas with panicked eyes, colorful pop art",
                    "comic book style hourglass draining rapidly with exclamation marks, vibrant cyan and magenta",
                    "person holding laptop with smoke coming out of ears in cartoon style, funny comic illustration",
                    "comic book panel with text 'EVERYTHING IS FINE' surrounded by harmless colorful cartoon flames"
                ]
            },
            {
                "number": 3,
                "name": "Part 3: The Rapid Descent Into Chaos",
                "title": "Part 3: The Rapid Descent Into Chaos",
                "voiceover": (
                    f"Suddenly, the reality of {clean_name} crashes through the wall like an uninvited wrecking ball. "
                    "All the meticulous little plans you made instantly disintegrate into pure, unadulterated chaotic pandemonium. "
                    "Your heart rate spikes, your brain opens forty-seven emergency anxiety tabs all at the same time, and logic completely abandons the room. "
                    "You find yourself standing completely frozen in the middle of your kitchen or office, staring blankly at a wall, wondering how your life choices brought you to this exact moment. "
                    "It is not just a mistake; it is an Olympic-level display of self-sabotage."
                ),
                "broll_prompts": [
                    "dramatic comic pop art close-up of panicked face with hands on cheeks, screaming like The Scream painting in Roy Lichtenstein style",
                    "comic explosion with bold words 'PANIC' in giant red letters, halftone dots, 9:16 vertical",
                    "comic character frantically rummaging through papers and clutter, flying documents, dynamic motion lines",
                    "person staring into empty refrigerator at night with funny bewildered comic expression"
                ]
            },
            {
                "number": 4,
                "name": "Part 4: The Awkward Social Hostage Situation",
                "title": "Part 4: The Awkward Social Hostage Situation",
                "voiceover": (
                    f"And of course, the worst part of {clean_name} is having to interact with other human beings while your soul is actively evaporating. "
                    "Someone approaches you and asks a completely normal, casual question, and your brain completely forgets how human speech works. "
                    "You just stand there nodding your head vigorously like a malfunctioning dashboard bobblehead, repeating 'totally, makes total sense' over and over. "
                    "You are sweating through three layers of clothing, praying for an earthquake or a sudden fire drill to provide a blessed escape. "
                    "Adulting is ninety percent pretending you know what you are doing while desperately hoping nobody asks follow-up questions."
                ),
                "broll_prompts": [
                    "two comic characters having awkward elevator conversation, sweat droplets flying, vibrant comic art",
                    "comic illustration of office water cooler with awkward characters staring in opposite directions",
                    "person smiling painfully with clenched teeth in comic pop art style, neon green and purple",
                    "comic speech bubble filled with nonsensical symbols and question marks, colorful pop art background"
                ]
            },
            {
                "number": 5,
                "name": "Part 5: Emergency Survival Protocols",
                "title": "Part 5: Emergency Survival Protocols",
                "voiceover": (
                    f"When dealing with the catastrophic aftermath of {clean_name}, standard etiquette must be immediately thrown out the window. "
                    "First protocol: The Phantom Phone Call. Tap your thigh, look at your blank phone screen with sudden immense urgency, whisper 'I have to take this,' and sprint away. "
                    "Second protocol: The Bathroom Hideout. Lock yourself in a stall for eleven peaceful minutes, breathing deeply and contemplating moving to an off-grid alpaca farm. "
                    "Third protocol: The Irish Exit. Slip through the nearest fire exit and disappear into the night like a slightly overweight, exhausted Batman. "
                    "Survival isn't pretty, ladies and gentlemen, but it works every single time."
                ),
                "broll_prompts": [
                    "comic superhero silhouette in modern streetwear leaping over fence into night, colorful comic book cover",
                    "person looking intensely at blank smartphone screen pretending to talk, funny comic pop art",
                    "comic illustration of closed restroom door with glowing sanctuary light, pop art halftone",
                    "comic character tip-toeing out of back exit into midnight shadows with triumphant smile"
                ]
            },
            {
                "number": 6,
                "name": "Part 6: Embracing The Chaos",
                "title": "Part 6: Embracing The Chaos",
                "voiceover": (
                    f"At the end of the day, {clean_name} teaches us the most liberating truth of modern life: absolutely nobody has it figured out. "
                    "We are all just winging it, pretending to be functional adults while quietly hoping nobody notices the wheels are falling off the wagon. "
                    "So forgive yourself for the chaos, drink your overpriced lukewarm coffee, and wear your everyday struggles like a badge of honor. "
                    f"If you survived this comedy deep dive and felt this in your soul, hit subscribe to {channel_name} and join our community of fellow chaotic survivors. "
                    "Drop your most embarrassing story in the comments below, and remember: reality is too ridiculous to take seriously."
                ),
                "broll_prompts": [
                    "Alex Miller laughing with oversized mug of coffee, pop art comic book cover aesthetic, neon colors",
                    "crowd of funny relatable comic characters cheering together, colorful confetti, vibrant pop art",
                    "comic book cover with giant title 'SURVIVED ANOTHER DAY', bold typography, Lichtenstein style",
                    "peaceful comic sunrise over city with funny pigeon wearing tiny sunglasses on ledge"
                ]
            }
        ]

        for ch in chapters:
            ch["script"] = ch["voiceover"]

        full_voiceover = " ".join([ch["voiceover"] for ch in chapters])
        hook_text = f"Why does {clean_name} actually turn into the most brutal everyday disaster that nobody warns you about?"
        top_image_prompts = [p for ch in chapters for p in ch.get("broll_prompts", [])][:6]
        return {
            "title": f"{title} | The Relatable Comedy Special",
            "title_card": "TOO REAL COMEDY",
            "hook": hook_text,
            "intro": chapters[0]["voiceover"],
            "chapters": chapters,
            "sections": [{"heading": ch["name"], "script": ch["voiceover"]} for ch in chapters],
            "outro": chapters[-1]["voiceover"],
            "cta": f"Subscribe to {channel_name} for daily relatable sanity.",
            "voiceover": full_voiceover,
            "image_prompts": top_image_prompts,
            "thumbnail_prompt": f"Comic pop art panicked face, neon yellow background, bold text {title[:30]}",
            "broll_keywords": [
                f"{topic} comic pop art",
                "funny relatable panicked expression comic",
                "office awkward conversation comic pop art",
                "running away like batman comic",
                "person coffee laughing comic book cover"
            ],
            "description": (
                f"{title}\n\n"
                f"A painfully accurate, satirical deep dive into {topic} and the absurdity of modern adulting.\n\n"
                "Chapters:\n" +
                "\n".join([f"0{i}:00 - {ch['name']}" for i, ch in enumerate(chapters, 1)]) +
                f"\n\nSubscribe to {channel_name} for more hilarious everyday truths."
            ),
            "hashtags": "#funny #relatable #comedy #humor #adulting #memes #workhumor #tooreal",
            "tags": ["funny", "relatable", "comedy", "humor", "adulting", "satire", "too real"]
        }

