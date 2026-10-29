    for row in valid_leads:
        idx = row["_row_index"]
        status = row.get("Status", "")
        currency = row.get("Currency", "USD") # Captures Cleva multi-currency preference
        
        try:
            # 1. Process New Clear Title Leads with Priority Queueing
            if status == "Clear Title":
                address = row.get("Property Address")
                city = row.get("City")
                country = row.get("Country")
                owner_name = row.get("Owner Name")
                owner_phone = row.get("Owner Phone")
                owner_email = row.get("Owner Email")
                arv = float(row.get("ARV", 0) or 0)
                repairs = float(row.get("Repairs", 0) or 0)
                asking_price = float(row.get("Asking Price", 0) or 0)

                print(f"Evaluating live priority governance for lead: {address}, {city} ({country}) [Currency: {currency}]")
                mao = (arv * 0.70) - repairs
                gross_spread = arv - repairs - asking_price

                if gross_spread > 0 and asking_price <= mao:
                    print(f"Underwriting Passed. Priority MAO calculated: ${mao:,.2f} {currency} (Spread: ${gross_spread:,.2f})")
                    pdf_filename = generate_pdf_contract(address, owner_name, mao)
                    
                    if pdf_filename:
                        try:
                            msg = EmailMessage()
                            msg['Subject'] = f"Official All-Cash Acquisition Offer - {address}"
                            msg['From'] = sender_email
                            msg['To'] = owner_email
                            msg.set_content(
                                f"Dear {owner_name},\n\nSovereign Grid Institutional Acquisitions has completed its "
                                f"underwriting for your property located at {address}, {city}, {country}.\n\n"
                                f"Our formal all-cash purchase offer is: ${mao:,.2f} {currency}\n\n"
                                f"Settlement framework: Cleva Multi-Currency Infrastructure ({currency}).\n\n"
                                "Please review the attached formal non-predatory purchase agreement and reply to accept.\n\n"
                                "Best regards,\nSovereign Grid Acquisitions Team"
                            )

                            with open(pdf_filename, 'rb') as f:
                                msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=f.name)

                            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                                server.starttls()
                                server.login(sender_email, sender_password)
                                server.send_message(msg)
                            print(f"Live acquisition offer dispatched securely to {owner_email}")
                        except Exception as email_err:
                            print(f"Email dispatch error for {address}: {email_err}")

                    telegram_msg = (
                        f"🌐 *SOVEREIGN GRID: LIVE OFFER DISPATCHED* 🌐\n\n"
                        f"📍 *Property:* `{address}, {city}, {country}`\n"
                        f"👤 *Owner:* {owner_name} ({owner_phone})\n"
                        f"💰 *Calculated MAO:* `${mao:,.2f} {currency}`\n"
                        f"📊 *Gross Spread:* `${gross_spread:,.2f}`\n"
                        f"🚀 *Status:* Live Institutional Offer Sent."
                    )
                    send_telegram_alert(telegram_msg)

                    # Update Status to column 15
                    sheet.update_cell(idx, 15, "Offer Sent")
                    print(f"Google Sheet row {idx} status successfully updated to 'Offer Sent'.")

                    if pdf_filename and os.path.exists(pdf_filename):
                        os.remove(pdf_filename)
                else:
                    print(f"Lead failed institutional governance thresholds. Gross Spread: ${gross_spread:,.2f}")

            # 2. Process Lifecycle Follow-Up State Management with Error Isolation
            elif status == "Offer Sent":
                address = row.get("Property Address")
                owner_name = row.get("Owner Name")
                print(f"Checking live lifecycle for pending offer: {address}")
                
                # Update Status to column 15
                sheet.update_cell(idx, 15, "Follow-Up Required")
                
                followup_msg = (
                    f"🔄 *SOVEREIGN GRID: LIVE FOLLOW-UP REQUIRED* 🔄\n\n"
                    f"📍 *Property:* `{address}`\n"
                    f"👤 *Owner:* {owner_name}\n"
                    f"⏱️ *Action:* Initial live offer pending response. Secondary re-engagement required."
                )
                send_telegram_alert(followup_msg)
                print(f"Row {idx} transitioned to 'Follow-Up Required'.")

        except Exception as row_error:
            print(f"Error processing row {idx} ({row.get('Property Address', 'Unknown')}): {row_error}")
            continue
                            
