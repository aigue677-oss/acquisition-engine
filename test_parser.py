from webhook_parser import parse_incoming_reply

# Simulate a seller replying with an acceptance
# (Replace with an actual owner email currently present in your Google Sheet)
test_email = "liamharford26@gmail.com" 
test_message = "Hello, we reviewed your offer and we gladly accept! Let's proceed with the agreement."

print("Simulating inbound seller response...")
result = parse_incoming_reply(test_email, test_message)
print("Simulation Result:", result)
