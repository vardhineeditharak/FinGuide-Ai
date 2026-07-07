# Unified Payments Interface (UPI): Standard Operating Guidelines and Security Protocol
*Published under the regulatory framework of the National Payments Corporation of India (NPCI).*

---

## 1. Technical Framework of UPI

**Unified Payments Interface (UPI)** is a real-time, single-window payment system developed by the **National Payments Corporation of India (NPCI)**. It allows instant inter-bank peer-to-peer (P2P) and peer-to-merchant (P2M) transactions.
* **Mechanism:** UPI merges multiple bank services, routing systems, and merchant checkout properties under a single mobile app, executing transfers instantly without the need for routing codes (IFSC) or static bank account numbers.

---

## 2. Operational Procedures

### A. Initiating Payments (Outward Remittance)
1. Launch any NPCI-registered PSP (Payment Service Provider) application (e.g., BHIM, bank app, Google Pay, PhonePe, Paytm).
2. The application registers your device and binds the cellular profile with the bank account registered to your phone number.
3. Establish a **UPI PIN** (4 or 6 digits) via debit card verification. This PIN operates as the primary cryptographic token to authorize debits.
4. Input the recipient's **UPI ID / VPA (Virtual Payment Address)** or scan the merchant's NPCI-compliant **QR Code**.
5. Verify the recipient's verified name displayed on the confirmation interface *before* entering the UPI PIN.
6. Submit the UPI PIN to authorize the transaction. The transaction completes instantly.

### B. Receiving Payments (Inward Remittance)
* **Crucial Security Standard:** Receiving money via UPI **never** requires entering your UPI PIN or scanning a QR code. 
* **Scam Indicator:** If any app or request prompts you to scan a QR code or submit a PIN to receive funds, it is a fraud attempt. These actions execute a payment debit from your account, not a credit.

---

## 3. Mandatory Security Directives

* **UPI PIN Confidentiality:** Never disclose your UPI PIN, account passwords, or bank SMS OTPs under any circumstances. Official PSP developers and banking networks do not request this data.
* **Biometric Locks:** Enable application-level biometric authentication (fingerprint/face recognition) to prevent unauthorized local app accesses.
* **UPI Lite Activation:** For low-value daily retail checkouts (under ₹500), configure UPI Lite. UPI Lite uses an on-device wallet, bypassing the core bank account access for small payments to limit exposure.
* **Verify Payment Requests:** Ignore and decline unsolicited "Collect Requests" received on your app unless you have actively initiated a purchase with that specific merchant.

---

## 4. Regulatory Limits and Transaction Controls

NPCI imposes strict daily guidelines to curb financial crime and limit exposure:
* **Standard Daily Cap:** The general regulatory limit is ₹1,00,000 per user within a 24-hour cycle. Higher caps (up to ₹5,00,000) are reserved for specific educational, healthcare, and utility merchant categories.
* **Velocity Limits:** Banks enforce their own transaction limits (typically between 10 to 20 transactions per day).
* **Cooling Period for New Registrations:** Upon new registration or changes in device profile, a mandatory cooling-off cap limits total transactions to ₹5,00,000 or lower for the first 24 hours. The first transaction is strictly capped at ₹5,000 as a fraud prevention control.

---

## 5. Dispute Resolution and Reversals

In the event of a failed transaction where funds are debited from the sender's account but not received by the recipient:

1. **Auto-Reversal System:** Most failed transactions undergo automatic reconciliation and are credited back to the source account within **24 to 48 hours**.
2. **PSP Application Redressal:** If the reversal is delayed, navigate to the transaction history inside the app and select "Raise Dispute" or "Raise Query".
3. **NPCI Escalation Portal:** If the PSP fails to resolve the dispute, customers can directly escalate the issue through the NPCI Dispute Redressal Mechanism on the official NPCI portal (**[npci.org.in](https://www.npci.org.in)**).
