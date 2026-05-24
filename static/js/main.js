// Utility function to format currency
const formatCurrency = (amount) => {
    return '$' + parseFloat(amount).toFixed(2);
};

// Utility function to show messages
const showMessage = (elementId, message, isSuccess) => {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = 'message ' + (isSuccess ? 'success' : 'error');
    setTimeout(() => {
        el.style.display = 'none';
        el.className = 'message';
    }, 5000);
};

// ==============================
// 1. AUTHENTICATION & LOGIN
// ==============================
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;

        try {
            const res = await fetch('/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            const data = await res.json();
            
            if (data.success) {
                if(data.role === 'admin') window.location.href = '/admin';
                else window.location.href = '/customer';
            } else {
                showMessage('loginMessage', data.message, false);
            }
        } catch (error) {
            showMessage('loginMessage', 'Network error. Please try again.', false);
        }
    });
}

function logout() {
    fetch('/logout', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        if(data.success) window.location.href = '/login';
    });
}

// ==============================
// 2. ADMIN FUNCTIONS
// ==============================
const createUserForm = document.getElementById('createUserForm');
if (createUserForm) {
    createUserForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = document.getElementById('newUsername').value;
        const password = document.getElementById('newPassword').value;
        const initial_balance = document.getElementById('newBalance').value;

        const res = await fetch('/admin/create_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, initial_balance })
        });
        const data = await res.json();
        
        showMessage('createUserMessage', 
            data.success ? `User created! Account No: ${data.account_number}` : data.message, 
            data.success
        );
        if(data.success) {
            createUserForm.reset();
            loadUsers();
        }
    });
}

const depositForm = document.getElementById('depositForm');
if (depositForm) {
    depositForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const account_number = document.getElementById('depositAccount').value;
        const amount = document.getElementById('depositAmount').value;

        const res = await fetch('/admin/deposit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ account_number, amount })
        });
        const data = await res.json();
        
        showMessage('depositMessage', data.message, data.success);
        if(data.success) {
            depositForm.reset();
            loadUsers();
            loadStaticAdminTransactions();
        }
    });
}

async function loadUsers() {
    const tableBody = document.querySelector('#usersTable tbody');
    if(!tableBody) return;
    
    const res = await fetch('/admin/users');
    const users = await res.json();
    if(users.success === false) return; // unauthorized or error
    
    tableBody.innerHTML = '';
    users.forEach(u => {
        tableBody.innerHTML += `
            <tr>
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td><strong>${u.account_number}</strong></td>
                <td>${formatCurrency(u.balance)}</td>
            </tr>
        `;
    });
}

async function loadStaticAdminTransactions() {
    const tableBody = document.querySelector('#adminTransactionsTable tbody');
    if(!tableBody) return;
    
    const res = await fetch('/admin/transactions');
    const tx = await res.json();
    if(tx.success === false) return;
    
    tableBody.innerHTML = '';
    tx.forEach(t => {
        tableBody.innerHTML += `
            <tr>
                <td>${new Date(t.timestamp).toLocaleString()}</td>
                <td>${t.sender_acc}</td>
                <td>${t.receiver_acc}</td>
                <td>${formatCurrency(t.amount)}</td>
            </tr>
        `;
    });
}

// ==============================
// 3. CUSTOMER FUNCTIONS
// ==============================
async function loadBalance() {
    const balanceEl = document.getElementById('userBalance');
    if(!balanceEl) return;
    
    const res = await fetch('/user/balance');
    const data = await res.json();
    
    if(data.success) {
        balanceEl.textContent = formatCurrency(data.balance);
    }
}

const transferForm = document.getElementById('transferForm');
if (transferForm) {
    transferForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const receiver_acc = document.getElementById('transferReceiver').value;
        const amount = document.getElementById('transferAmount').value;

        const res = await fetch('/user/transfer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ receiver_acc, amount })
        });
        const data = await res.json();
        
        showMessage('transferMessage', data.message, data.success);
        if(data.success) {
            transferForm.reset();
            loadBalance();
            loadHistory();
        }
    });
}

async function loadHistory() {
    const tableBody = document.querySelector('#historyTable tbody');
    if(!tableBody) return;
    
    const res = await fetch('/user/history');
    const tx = await res.json();
    if(tx.success === false) return;
    
    tableBody.innerHTML = '';
    tx.forEach(t => {
        tableBody.innerHTML += `
            <tr>
                <td>${new Date(t.timestamp).toLocaleString()}</td>
                <td>${t.sender_acc}</td>
                <td>${t.receiver_acc}</td>
                <td>${formatCurrency(t.amount)}</td>
            </tr>
        `;
    });
}
