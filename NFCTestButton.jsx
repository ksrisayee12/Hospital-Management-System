function NFCTestButton() {
  const sendScan = async () => {
    const res = await fetch(`http://${window.location.hostname}:5000/api/nfc/scan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        doctor_code: "DOC001",
        nfc_uid: "TEST_NFC_001",
        patient_id: "PAT001",
        action: "CHECK_IN",
        scanned_from: "mobile"
      })
    });

    const data = await res.json();
    alert(JSON.stringify(data));
  };

  return <button onClick={sendScan}>Test NFC Scan</button>;
}

export default NFCTestButton;
