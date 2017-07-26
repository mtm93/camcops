/*
    Copyright (C) 2012-2017 Rudolf Cardinal (rudolf@pobox.com).

    This file is part of CamCOPS.

    CamCOPS is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CamCOPS is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CamCOPS. If not, see <http://www.gnu.org/licenses/>.
*/

#include "camcopsversion.h"

namespace camcopsversion {  // http://semver.org/

const Version CAMCOPS_VERSION(2, 0, 1);
const Version MINIMUM_SERVER_VERSION(2, 0, 0);

}  // namespace camcopsversion

/*

===============================================================================
VERSION HISTORY
===============================================================================
2.0.0
- Development of C++ version from scratch. Replaces Titanium version.
- Released as beta to Google Play on 2017-07-17.

2.0.1
- More const checking.
- Bugfix to stone/pound/ounce conversion.
- Bugfix to raw SQL dump.
- ID numbers generalized so you can have >8 (= table structure change).

*/
