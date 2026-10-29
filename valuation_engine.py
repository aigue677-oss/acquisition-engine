def calculate_heuristic_arv(square_footage: float, market_ppsf: float = 150.0) -> float:
    """
    Calculates an estimated After Repair Value (ARV) internally 
    using a localized Price-Per-Square-Foot (PPSF) baseline.
    """
    if not square_footage or square_footage <= 0:
        # Fallback baseline square footage if not specified in lead payload
        square_footage = 1500.0 
    
    estimated_arv = square_footage * market_ppsf
    return estimated_arv

def calculate_dynamic_mao(arv: float, estimated_repairs: float, target_wholesale_fee: float = 10000.0) -> float:
    """
    Calculates the institutional-grade Maximum Allowable Offer (MAO)
    Formula: (ARV * 0.70) - Repairs - Wholesale Fee
    """
    standard_discount_arv = arv * 0.70
    mao = standard_discount_arv - estimated_repairs - target_wholesale_fee
    return max(mao, 0.0)
  
