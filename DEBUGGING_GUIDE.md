"""
DEBUGGING GUIDE - Election Selection Duplicate Vote Check

The code is deployed correctly, but let's verify it's actually working as expected.

STEP 1: Verify Browser is NOT Caching Old Code
====================================================================
1. Open browser DevTools (F12)
2. Go to Application → Cache Storage → Clear All
3. Go to Application → IndexedDB → Clear All  
4. Do a HARD REFRESH: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
5. Try the flow again

STEP 2: Test with Isha Chopra (Real Voter Who Has Voted)
====================================================================
Mobile: 7710611913
Election: 2026-motiahuys

Flow:
1. Open voting system
2. Enter mobile: 7710611913
3. Any OTP (system sends real SMS, or you can use placeholder)
4. Click on "2026-motiahuys" election
5. **EXPECTED**: Error message on election selection screen, no voting section

STEP 3: Check Browser Console (F12)
====================================================================
When you click on the election, look for these console messages:

✓ Should see:
  "Checking if user can vote in election: 2026-motiahuys"
  "Error during election selection"

✗ Should NOT see:
  "User can vote - proceeding to voting interface"

STEP 4: Check Network Tab (F12 → Network)
====================================================================
After clicking election, look for a POST request to /auth/send-otp

Request body should include:
{
    "mobileNumber": "7710611913",
    "electionId": "2026-motiahuys"
}

Response should be:
{
    "errorCode": "ALREADY_VOTED",
    "message": "You have already voted in this election. You cannot vote again."
}

STEP 5: Verify Error Message Displays
====================================================================
After clicking election for Isha Chopra:
- Election selection screen should stay visible
- Error message should appear on this screen
- Voting section should NOT open

If voting section opens despite the error:
====================================================================
This means selectElection() is NOT working correctly. Possible causes:

1. Browser cache (see STEP 1)
2. Object not found error - maybe 'votingClient' is not initialized
3. API call is succeeding when it should fail
4. Error message doesn't match "already voted" pattern

===================================================================
CRITICAL TEST: Run this in browser console to verify setup
===================================================================

Copy and paste this into browser console (F12):
--------
console.log("Checking votingClient:", typeof votingClient);
console.log("API Endpoint:", votingClient.API_ENDPOINT);
votingClient.apiCall('/elections', 'GET').then(r => {
    console.log("API Working:", r.success);
    console.log("Elections found:", r.data?.length);
}).catch(e => {
    console.error("API Error:", e.message);
});
--------

This should show:
✓ votingClient is function
✓ API Endpoint is https://vxvqzxd6rb.execute-api.ap-south-1.amazonaws.com/prod
✓ API Working: true
✓ Elections found: 1+ numbers

===================================================================
CRITICAL TEST: Manually test selectElection
===================================================================

Set mobile number in form:
--------
document.getElementById('mobileNumber').value = '7710611913';
--------

Then test selectElection with election ID:
--------
votingClient.selectElection('2026-motiahuys').then(() => {
    console.log("selectElection completed");
}).catch(e => {
    console.error("selectElection error:", e.message);
});
--------

This should:
✓ Show error on electionMessage element
✓ Keep user on electionSection
✗ NOT show votingSection

===================================================================
Report back with:
1. Results of STEP 1 (cache clearing)
2. Console messages from STEP 3
3. Network request/response from STEP 4
4. Manual test results from console tests above
===================================================================
"""
print(__doc__)
