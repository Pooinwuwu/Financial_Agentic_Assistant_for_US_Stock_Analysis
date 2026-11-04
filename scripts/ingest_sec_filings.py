import os
import json
import numpy as np
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHUNKS_FILE = DATA_DIR / "sec_chunks.json"

load_dotenv(BASE_DIR / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

# Curated SEC 10-K filings extracts (Item 1A Risk Factors & Item 7 MD&A) for the 10 target equities
SEC_DOCS = [
    # 1. AAPL
    {
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Global Supply Chain & Geopolitical Vulnerabilities",
        "content": (
            "The Company’s operations, business, and financial condition depend substantially on global manufacturing partners, "
            "with a substantial majority of final assembly facilities and component sourcing concentrated in the Asia-Pacific region, "
            "particularly mainland China, India, and Taiwan. Geopolitical tensions, trade conflicts, tariffs, or military conflict in the Taiwan Strait "
            "could disrupt supply chains and substantially decrease product shipments. Furthermore, single-source dependencies for key semiconductor "
            "silicon—including A-series and M-series chips fabricated exclusively by TSMC—expose the Company to operational disruption, yield shortages, "
            "and natural disaster risks that cannot be readily mitigated in the short term."
        )
    },
    {
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Services Growth & Regulatory Headwinds",
        "content": (
            "Net sales in the Services segment grew 13% year-over-year, driven by increases in advertising, cloud services, and App Store revenue. "
            "However, operating margins face sustained regulatory scrutiny. The European Union's Digital Markets Act (DMA) mandates structural alterations "
            "to iOS app distribution, alternative browser engines, and external payment links, impacting commission rates. Ongoing antitrust litigation "
            "with the United States Department of Justice challenging ecosystem exclusivity could adversely affect customer retention, developer fees, "
            "and gross margins across the Services segment in future fiscal years."
        )
    },

    # 2. MSFT
    {
        "ticker": "MSFT",
        "company": "Microsoft Corporation",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - AI Infrastructure Constraints & OpenAI Partnership",
        "content": (
            "Our strategic focus on generative AI and intelligent cloud depends significantly on commercial partnerships, particularly our strategic "
            "collaboration with OpenAI. Disruptions to this relationship, changes in governance, or operational divergence could impair our AI product pipeline. "
            "Additionally, scaling cloud and AI workloads via Azure requires enormous capital expenditures in specialized accelerator hardware, liquid-cooled "
            "data centers, and electrical grid power availability. Third-party GPU supply shortages or delays in data center construction could limit our capacity "
            "to fulfill surging cloud AI customer demand, resulting in lost market share and compressed operating margins."
        )
    },
    {
        "ticker": "MSFT",
        "company": "Microsoft Corporation",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Azure Cloud and Office 365 Commercial Momentum",
        "content": (
            "Intelligent Cloud revenue grew 19% to $105.4 billion, propelled by Azure and other cloud services growth of 30%. Commercial bookings rose 17%, "
            "reflecting long-term enterprise commitments to Microsoft Cloud and Copilot productivity add-ons. Operating income expanded 24% to $109.4 billion. "
            "Capital expenditures, including finance leases, increased substantially to $55.7 billion to support cloud and AI infrastructure buildout. "
            "Management anticipates continued elevated capital allocation to AI server capacity throughout fiscal 2025."
        )
    },

    # 3. NVDA
    {
        "ticker": "NVDA",
        "company": "NVIDIA Corporation",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - US Export Controls & Customer Concentration",
        "content": (
            "Our business is intensely sensitive to US government export control regulations governing advanced computing chips and semiconductor manufacturing equipment. "
            "Regulations revised in October 2023 restrict the shipment of our high-performance GPUs (including A100, H100, A800, and H800 architectures) to China "
            "and other restricted destinations without an explicit license. Historically, China represented 20-25% of our Data Center revenue; regulatory restrictions "
            "have caused our sales in this geographic region to decrease significantly. Furthermore, our Data Center revenue exhibits substantial customer concentration, "
            "with a small number of cloud hyperscalers accounting for a large percentage of total purchases."
        )
    },
    {
        "ticker": "NVDA",
        "company": "NVIDIA Corporation",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Data Center Hyper-Growth & Hopper Architecture",
        "content": (
            "Fiscal year 2024 revenue surged 126% to a record $60.9 billion, driven by extraordinary demand for our accelerated computing and generative AI platforms. "
            "Data Center revenue surged 217% to $47.5 billion, reflecting adoption of NVIDIA HGX systems based on the Hopper architecture (H100). Gross margin expanded "
            "to 72.7% from 56.9% in the prior fiscal year, reflecting favorable product mix and operational leverage. Transition to the next-generation Blackwell "
            "architecture platform is underway, with customer demand substantially exceeding initial production supply."
        )
    },

    # 4. AMD
    {
        "ticker": "AMD",
        "company": "Advanced Micro Devices, Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Intense Competition with NVIDIA and Foundry Reliance",
        "content": (
            "We face intense competition across all product lines, most acutely from NVIDIA in discrete GPUs and AI data center accelerators, and from Intel "
            "in x86 server and client processors. Competitors possess greater financial, marketing, and R&D resources, as well as dominant software ecosystem lock-in "
            "(e.g., CUDA). In addition, we rely entirely on third-party foundries, primarily TSMC, for the wafer fabrication of all our advanced 5nm, 4nm, and 3nm products. "
            "Any foundry supply allocations, packaging bottlenecks (such as CoWoS advanced packaging capacity), or wafer price increases could severely limit our ability "
            "to ship Instinct MI300 series accelerators."
        )
    },
    {
        "ticker": "AMD",
        "company": "Advanced Micro Devices, Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Data Center Segment and EPYC Adoption",
        "content": (
            "Data Center segment revenue grew 37% to $6.5 billion in fiscal 2023, driven by strong growth in 4th Gen AMD EPYC server CPUs and the initial commercial launch "
            "of Instinct MI300X AI accelerators. Client segment revenue declined 25% due to PC market softness, while Gaming segment revenue decreased 9% due to semi-custom "
            "console cycle maturation. We expect our Data Center and AI business to represent our largest growth catalyst in 2024, led by hyperscale cloud cluster deployments "
            "of MI300 GPUs."
        )
    },

    # 5. GOOGL
    {
        "ticker": "GOOGL",
        "company": "Alphabet Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Antitrust Enforcement & Generative Search Disruption",
        "content": (
            "Alphabet faces unprecedented regulatory enforcement and antitrust lawsuits from the US Department of Justice and global competition authorities regarding our "
            "search distribution agreements and advertising technology stack. Adverse rulings could mandate structural remedies, terminate default search agreements on major "
            "smartphones, or restrict ad exchange integration. Additionally, the evolution of search interfaces toward generative AI summaries presents uncertainty for "
            "search query monetization, click-through rates, and server cost economics, as inference cost per query is significantly higher than traditional indexing."
        )
    },
    {
        "ticker": "GOOGL",
        "company": "Alphabet Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Google Cloud Operating Profitability & AI Integration",
        "content": (
            "Alphabet consolidated revenues reached $307.4 billion in 2023, an increase of 9% year-over-year. Google Cloud delivered $33.1 billion in revenue, up 26%, "
            "and achieved full-year operating profitability of $1.7 billion compared to an operating loss of $3.0 billion in 2022. Google Services operating margin remained "
            "solid at 35%. We are actively integrating Gemini foundational models across Google Search, Workspace, YouTube, and Google Cloud, supporting sustained user "
            "engagement while exercising disciplined expense management."
        )
    },

    # 6. AMZN
    {
        "ticker": "AMZN",
        "company": "Amazon.com, Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - AWS Growth Deceleration & Fulfillment Labor Dynamics",
        "content": (
            "AWS revenue growth has experienced fluctuations as enterprise clients optimize cloud budgets and seek cost efficiencies. Heightened competition from Azure "
            "and Google Cloud in AI workload hosting could impact pricing and market share. Concurrently, our retail fulfillment operations are subject to regional wage pressure, "
            "unionization initiatives, transportation fuel volatility, and complex international trade regulations. Any disruption in logistics hubs or automation robotics "
            "could impair Prime delivery delivery promises and customer retention."
        )
    },
    {
        "ticker": "AMZN",
        "company": "Amazon.com, Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Regionalized Logistics Network & AWS Re-acceleration",
        "content": (
            "Net sales increased 12% to $574.8 billion in 2023. Operating income increased substantially to $36.9 billion, compared to $12.2 billion in 2022, "
            "driven by the successful transition of our US fulfillment network from a single national model to eight regional networks. This regionalization lowered "
            "cost-to-serve and reduced transport distances. AWS net sales rose 13% to $90.8 billion, with accelerating AI demand toward year-end as customers adopted Amazon Bedrock "
            "and custom Trainium and Inferentia chips."
        )
    },

    # 7. WMT
    {
        "ticker": "WMT",
        "company": "Walmart Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Consumer Spending Shifts & Grocery Margin Vulnerability",
        "content": (
            "Persistent consumer price inflation and elevated interest rates have shifted consumer spending patterns disproportionately toward food and consumables, "
            "which carry significantly lower gross profit margins than discretionary general merchandise (such as apparel and home electronics). Shrinkage (inventory theft) "
            "and supply chain logistics costs continue to impact gross margins. Furthermore, expanding our omni-channel automated distribution network requires substantial capital "
            "and exposes us to technology implementation risks across more than 10,000 retail units globally."
        )
    },
    {
        "ticker": "WMT",
        "company": "Walmart Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Omni-channel Retail & Advertising (Walmart Connect)",
        "content": (
            "Total revenue for fiscal 2024 increased 6.0% to $648.1 billion, with Walmart US comparable sales growing 5.6%. Global eCommerce sales increased 23%, "
            "surpassing $100 billion. High-margin growth businesses expanded rapidly: global advertising revenue (Walmart Connect) grew 28% to approximately $3.4 billion, "
            "and Walmart+ membership income expanded. Consolidated operating income grew 32.2% to $27.0 billion, demonstrating strong operating leverage across our supply chain."
        )
    },

    # 8. META
    {
        "ticker": "META",
        "company": "Meta Platforms, Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Reality Labs Losses & AI CapEx Commitments",
        "content": (
            "We continue to invest heavily in long-term strategic initiatives, including augmented and virtual reality through Reality Labs, which incurred an operating loss "
            "of $16.1 billion in 2023 and is expected to increase losses in 2024. Additionally, building industry-leading AI infrastructure and training Llama foundational models "
            "has sharply increased our planned capital expenditures. If our investments in generative AI and metaverse hardware fail to generate proportionate enterprise or "
            "consumer monetization, our long-term operating profitability and free cash flow generation will be severely impaired."
        )
    },
    {
        "ticker": "META",
        "company": "Meta Platforms, Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - 'Year of Efficiency' & Ad Impression Growth",
        "content": (
            "Total revenue increased 16% to $134.9 billion in 2023, while total costs and expenses decreased 1% as a result of our 'Year of Efficiency' restructuring initiatives, "
            "which included organizational consolidation and facility rationalization. Operating income rose 62% to $46.8 billion, expanding operating margin to 35%. "
            "Ad impressions across our Family of Apps increased 28%, benefiting from AI-powered recommendation systems (Advantage+ ad suites) and monetization improvements "
            "in Instagram Reels."
        )
    },

    # 9. TSLA
    {
        "ticker": "TSLA",
        "company": "Tesla, Inc.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Global EV Price Wars & Full Self-Driving Regulatory Risks",
        "content": (
            "The electric vehicle market has entered an era of aggressive price competition, particularly in China and Europe, from low-cost domestic manufacturers. "
            "To maintain volume growth, we implemented multiple price reductions, which resulted in significant automotive gross margin compression throughout 2023 and 2024. "
            "Additionally, our vehicle autonomy strategy relies on Full Self-Driving (FSD) Supervised. FSD is subject to intense regulatory investigation by the National Highway "
            "Traffic Safety Administration (NHTSA) and state regulators. Any mandated software recalls, liability findings, or regulatory prohibition against unsupervised "
            "commercial Robotaxi deployment would undermine our core valuation thesis."
        )
    },
    {
        "ticker": "TSLA",
        "company": "Tesla, Inc.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - Vehicle Deliveries & Energy Storage Surge",
        "content": (
            "Total automotive revenue reached $82.4 billion in 2023, up 15% year-over-year, driven by 1.81 million vehicle deliveries. However, automotive gross margin "
            "excluding regulatory credits dropped to 17.1% from 26.2% in 2022 due to price cuts. Conversely, Energy Generation and Storage revenue surged 125% to $6.0 billion, "
            "with Megapack deployments reaching record levels of 14.7 GWh. We continue to allocate capital toward next-generation vehicle architecture and 4680 battery cell scaling."
        )
    },

    # 10. JPM
    {
        "ticker": "JPM",
        "company": "JPMorgan Chase & Co.",
        "fiscal_year": 2024,
        "section": "Item 1A",
        "section_title": "Risk Factors - Interest Rate Volatility & Basel III Endgame Capital Rules",
        "content": (
            "JPMorgan Chase’s revenue and net interest income are highly sensitive to Federal Reserve monetary policy, inflation, and yield curve shifts. Rapid declines in benchmark "
            "interest rates would compress net interest margins on our deposit base. Furthermore, regulatory proposals under the 'Basel III Endgame' would significantly increase risk-weighted "
            "asset calculations and mandate higher Tier 1 Common Equity capital buffers for global systemically important banks (G-SIBs). These rules could constrain return on equity (ROE), "
            "restrict share repurchases, and reduce lending flexibility in commercial real estate and trading desks."
        )
    },
    {
        "ticker": "JPM",
        "company": "JPMorgan Chase & Co.",
        "fiscal_year": 2024,
        "section": "Item 7",
        "section_title": "Management's Discussion and Analysis - First Republic Acquisition & Record Net Income",
        "content": (
            "JPMorgan Chase reported record net income of $49.6 billion for 2023, up 32% year-over-year, with return on tangible common equity (ROTCE) of 21%. Net revenue rose 23% "
            "to $158.1 billion, driven by Net Interest Income of $89.3 billion resulting from higher rates and the acquisition of First Republic Bank. Credit costs were $9.3 billion, "
            "reflecting reserve builds for office commercial real estate and higher credit card net charge-offs as consumer liquidity normalized."
        )
    }
]

def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 180) -> list[str]:
    """Windowed passage chunking with character-level approximation of ~300 tokens and ~15% overlap."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        if end >= len(text):
            break
        start += (chunk_size - overlap)
    return chunks

def build_sec_vector_store():
    print(f"Ingesting SEC 10-K filings into vector index...")
    all_chunks = []
    chunk_counter = 1

    for doc in SEC_DOCS:
        ticker = doc["ticker"]
        fy = doc["fiscal_year"]
        sec = doc["section"]
        title = doc["section_title"]
        raw_text = f"{doc['company']} ({ticker}) Fiscal Year {fy} - {sec}: {title}.\n{doc['content']}"
        
        passages = chunk_text(raw_text, chunk_size=900, overlap=150)
        for idx, passage in enumerate(passages):
            chunk_id = f"{ticker}_{fy}_{sec.replace(' ', '')}_c{idx+1}"
            all_chunks.append({
                "id": chunk_id,
                "ticker": ticker,
                "company": doc["company"],
                "fiscal_year": fy,
                "section": sec,
                "title": title,
                "text": passage
            })

    print(f"Total passages created: {len(all_chunks)}. Computing bge-m3 embeddings...")

    # Embed in batches using class proxy bge-m3
    batch_size = 10
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i+batch_size]
        texts = [b["text"] for b in batch]
        try:
            resp = client.embeddings.create(
                model="bge-m3",
                input=texts
            )
            for j, data_obj in enumerate(resp.data):
                batch[j]["embedding"] = data_obj.embedding
            print(f"  Embedded passages {i+1} to {min(i+batch_size, len(all_chunks))}...")
        except Exception as e:
            print(f"  Error embedding batch starting at {i}: {e}")
            raise e

    # Save to disk
    with open(CHUNKS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\nVector index successfully generated and saved to: {CHUNKS_FILE}")
    print(f"Total indexed chunks: {len(all_chunks)} with 1024-dim bge-m3 vectors.")

if __name__ == "__main__":
    build_sec_vector_store()
